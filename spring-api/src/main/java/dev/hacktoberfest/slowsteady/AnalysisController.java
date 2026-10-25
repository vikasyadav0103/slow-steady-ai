package dev.hacktoberfest.slowsteady;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
public class AnalysisController {
    private final RestClient aiClient;

    public AnalysisController(@Value("${ai.service-url:http://localhost:8000}") String aiServiceUrl) {
        this.aiClient = RestClient.builder().baseUrl(aiServiceUrl).build();
    }

    @PostMapping(value = "/analyze", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public AnalysisResponse analyze(@Valid @RequestBody AnalysisRequest request) {
        try {
            AnalysisResponse response = aiClient.post().uri("/analyze").contentType(MediaType.APPLICATION_JSON)
                    .body(request).retrieve().body(AnalysisResponse.class);
            if (response == null) throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "AI service returned an empty response");
            return response;
        } catch (RestClientException exception) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "AI service is unavailable", exception);
        }
    }

    public record AnalysisRequest(@NotBlank @Size(min = 20, max = 20000) String text,
                                  @Min(1) @Max(8) Integer max_sentences) {
        public AnalysisRequest {
            if (max_sentences == null) max_sentences = 3;
        }
    }

    public record AnalysisResponse(String summary, List<String> action_items,
                                   int duplicate_sentence_count, String mode) {}
}
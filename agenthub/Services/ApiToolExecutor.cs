using System.Net.Http;
using System.Text;
using System.Text.Json;

namespace AIAgentManagement.Services;

public class ApiToolExecutor : IApiToolExecutor
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<ApiToolExecutor> _logger;

    public ApiToolExecutor(IHttpClientFactory httpClientFactory, ILogger<ApiToolExecutor> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<string> ExecuteAsync(string config, string? inputData)
    {
        try
        {
            var configObj = JsonSerializer.Deserialize<ApiToolConfig>(config);
            if (configObj == null)
            {
                throw new InvalidOperationException("Invalid API tool configuration");
            }

            if (string.IsNullOrEmpty(configObj.Url))
            {
                throw new InvalidOperationException("API tool URL is required");
            }

            var httpClient = _httpClientFactory.CreateClient();
            httpClient.Timeout = TimeSpan.FromSeconds(30);

            // 헤더 설정
            if (configObj.Headers != null)
            {
                foreach (var header in configObj.Headers)
                {
                    httpClient.DefaultRequestHeaders.TryAddWithoutValidation(header.Key, header.Value);
                }
            }

            // 인증 설정
            if (!string.IsNullOrEmpty(configObj.AuthType))
            {
                switch (configObj.AuthType.ToLower())
                {
                    case "apikey":
                        if (!string.IsNullOrEmpty(configObj.ApiKey))
                        {
                            var keyHeader = configObj.ApiKeyHeader ?? "X-API-Key";
                            if (!string.IsNullOrEmpty(keyHeader))
                            {
                                httpClient.DefaultRequestHeaders.TryAddWithoutValidation(keyHeader, configObj.ApiKey);
                            }
                        }
                        break;

                    case "bearer":
                        if (!string.IsNullOrEmpty(configObj.BearerToken))
                        {
                            httpClient.DefaultRequestHeaders.Authorization = 
                                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", configObj.BearerToken);
                        }
                        break;
                }
            }

            HttpRequestMessage request;
            var method = configObj.Method?.ToUpper() ?? "GET";

            if (method == "GET")
            {
                var url = configObj.Url;
                if (!string.IsNullOrEmpty(inputData) && configObj.AppendInputAsQuery)
                {
                    var inputObj = JsonSerializer.Deserialize<Dictionary<string, object>>(inputData);
                    if (inputObj != null)
                    {
                        var queryString = string.Join("&", inputObj.Select(kvp => $"{kvp.Key}={Uri.EscapeDataString(kvp.Value?.ToString() ?? "")}"));
                        url += (url.Contains("?") ? "&" : "?") + queryString;
                    }
                }

                request = new HttpRequestMessage(HttpMethod.Get, url);
            }
            else
            {
                request = new HttpRequestMessage(new HttpMethod(method), configObj.Url);

                if (!string.IsNullOrEmpty(inputData))
                {
                    var contentType = configObj.ContentType ?? "application/json";
                    request.Content = new StringContent(inputData, Encoding.UTF8, contentType);
                }
            }

            var response = await httpClient.SendAsync(request);
            var responseContent = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                return JsonSerializer.Serialize(new
                {
                    success = false,
                    statusCode = (int)response.StatusCode,
                    error = responseContent
                });
            }

            return JsonSerializer.Serialize(new
            {
                success = true,
                statusCode = (int)response.StatusCode,
                data = responseContent
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing API tool");
            return JsonSerializer.Serialize(new { success = false, error = ex.Message });
        }
    }

    private class ApiToolConfig
    {
        public string? Url { get; set; }
        public string? Method { get; set; }
        public Dictionary<string, string>? Headers { get; set; }
        public string? AuthType { get; set; }
        public string? ApiKey { get; set; }
        public string? ApiKeyHeader { get; set; }
        public string? BearerToken { get; set; }
        public string? ContentType { get; set; }
        public bool AppendInputAsQuery { get; set; }
    }
}

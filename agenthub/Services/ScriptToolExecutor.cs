using System.Diagnostics;
using System.Text.Json;

namespace AIAgentManagement.Services;

public class ScriptToolExecutor : IScriptToolExecutor
{
    private readonly ILogger<ScriptToolExecutor> _logger;
    private const int MaxExecutionTimeMs = 30000; // 30초

    public ScriptToolExecutor(ILogger<ScriptToolExecutor> logger)
    {
        _logger = logger;
    }

    public async Task<string> ExecuteAsync(string language, string code, string? inputData)
    {
        try
        {
            string executable;
            string extension;

            switch (language.ToLower())
            {
                case "python":
                    executable = "python";
                    extension = ".py";
                    break;

                case "javascript":
                case "js":
                    executable = "node";
                    extension = ".js";
                    break;

                default:
                    throw new NotSupportedException($"Language '{language}' is not supported");
            }

            // 임시 파일 생성
            var tempFile = Path.Combine(Path.GetTempPath(), $"tool_{Guid.NewGuid()}{extension}");
            
            try
            {
                // 입력 데이터를 환경변수나 파일로 전달
                var inputFile = Path.Combine(Path.GetTempPath(), $"input_{Guid.NewGuid()}.json");
                await File.WriteAllTextAsync(inputFile, inputData ?? "{}");

                // 코드 작성 (입력 파일 읽기 포함)
                string wrappedCode;
                if (language.ToLower() == "python")
                {
                    wrappedCode = $@"
import json
import sys

# 입력 데이터 읽기
with open('{inputFile.Replace("\\", "\\\\")}', 'r', encoding='utf-8') as f:
    input_data = json.load(f)

# 사용자 코드
{code}

# 결과 출력
result = {{""success"": True}}
print(json.dumps(result))
";
                }
                else // JavaScript
                {
                    wrappedCode = $@"
const fs = require('fs');
const inputData = JSON.parse(fs.readFileSync('{inputFile.Replace("\\", "/")}', 'utf8'));

// 사용자 코드
{code}

// 결과 출력
const result = {{success: true}};
console.log(JSON.stringify(result));
";
                }

                await File.WriteAllTextAsync(tempFile, wrappedCode);

                // 프로세스 실행
                var processInfo = new ProcessStartInfo
                {
                    FileName = executable,
                    Arguments = language.ToLower() == "python" 
                        ? $"\"{tempFile}\"" 
                        : $"\"{tempFile}\"",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = new Process { StartInfo = processInfo };
                var outputBuilder = new System.Text.StringBuilder();
                var errorBuilder = new System.Text.StringBuilder();

                process.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        outputBuilder.AppendLine(e.Data);
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        errorBuilder.AppendLine(e.Data);
                };

                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                var completed = await Task.Run(() => process.WaitForExit(MaxExecutionTimeMs));

                if (!completed)
                {
                    process.Kill();
                    throw new TimeoutException($"Script execution exceeded maximum time limit of {MaxExecutionTimeMs}ms");
                }

                if (process.ExitCode != 0)
                {
                    var error = errorBuilder.ToString();
                    return JsonSerializer.Serialize(new { success = false, error = error });
                }

                var output = outputBuilder.ToString().Trim();
                return string.IsNullOrEmpty(output) ? "{}" : output;
            }
            finally
            {
                // 임시 파일 정리
                try
                {
                    if (File.Exists(tempFile))
                        File.Delete(tempFile);
                }
                catch { }

                try
                {
                    var inputFile = Path.Combine(Path.GetTempPath(), $"input_{Guid.NewGuid()}.json");
                    if (File.Exists(inputFile))
                        File.Delete(inputFile);
                }
                catch { }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing {Language} script", language);
            return JsonSerializer.Serialize(new { success = false, error = ex.Message });
        }
    }
}

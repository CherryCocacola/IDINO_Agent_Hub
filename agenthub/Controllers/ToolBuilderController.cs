using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using AIAgentManagement.DTOs;
using AIAgentManagement.Services;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ToolBuilderController : ControllerBase
{
    private readonly ICSharpToolExecutor _csharpExecutor;
    private readonly IScriptToolExecutor _scriptExecutor;
    private readonly ILogger<ToolBuilderController> _logger;

    public ToolBuilderController(
        ICSharpToolExecutor csharpExecutor,
        IScriptToolExecutor scriptExecutor,
        ILogger<ToolBuilderController> logger)
    {
        _csharpExecutor = csharpExecutor;
        _scriptExecutor = scriptExecutor;
        _logger = logger;
    }

    [HttpPost("compile")]
    public async Task<ActionResult<CompileResultDto>> CompileCode([FromBody] CompileCodeRequestDto request)
    {
        try
        {
            if (string.IsNullOrEmpty(request.Code))
            {
                return BadRequest(ErrorResponseDto.BadRequest("Code is required"));
            }

            var errors = new List<string>();

            switch (request.Language?.ToLower())
            {
                case "csharp":
                case "c#":
                    errors = ValidateCSharpCode(request.Code);
                    break;

                case "python":
                case "javascript":
                case "js":
                    // Python/JavaScript는 런타임 검증만 가능
                    break;

                default:
                    return BadRequest(ErrorResponseDto.BadRequest($"Language '{request.Language}' is not supported for compilation"));
            }

            return Ok(new CompileResultDto
            {
                Success = errors.Count == 0,
                Errors = errors
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error compiling code");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("validate")]
    public async Task<ActionResult<ValidateResultDto>> ValidateCode([FromBody] ValidateCodeRequestDto request)
    {
        try
        {
            if (string.IsNullOrEmpty(request.Code))
            {
                return BadRequest(ErrorResponseDto.BadRequest("Code is required"));
            }

            var warnings = new List<string>();
            var errors = new List<string>();

            // 기본 검증
            if (request.Code.Length > 100000) // 100KB 제한
            {
                errors.Add("Code exceeds maximum size limit of 100KB");
            }

            // 언어별 검증
            switch (request.Language?.ToLower())
            {
                case "csharp":
                case "c#":
                    errors.AddRange(ValidateCSharpCode(request.Code));
                    break;

                case "python":
                    warnings.AddRange(ValidatePythonCode(request.Code));
                    break;

                case "javascript":
                case "js":
                    warnings.AddRange(ValidateJavaScriptCode(request.Code));
                    break;

                default:
                    return BadRequest(ErrorResponseDto.BadRequest($"Language '{request.Language}' is not supported"));
            }

            return Ok(new ValidateResultDto
            {
                Valid = errors.Count == 0,
                Errors = errors,
                Warnings = warnings
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error validating code");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpPost("test")]
    public async Task<ActionResult<TestResultDto>> TestCode([FromBody] TestCodeRequestDto request)
    {
        try
        {
            if (string.IsNullOrEmpty(request.Code))
            {
                return BadRequest(ErrorResponseDto.BadRequest("Code is required"));
            }

            string result;

            switch (request.Language?.ToLower())
            {
                case "csharp":
                case "c#":
                    result = await _csharpExecutor.ExecuteAsync(request.Code, request.InputData);
                    break;

                case "python":
                case "javascript":
                case "js":
                    result = await _scriptExecutor.ExecuteAsync(request.Language, request.Code, request.InputData);
                    break;

                default:
                    return BadRequest(ErrorResponseDto.BadRequest($"Language '{request.Language}' is not supported"));
            }

            return Ok(new TestResultDto
            {
                Success = true,
                Output = result
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error testing code");
            return Ok(new TestResultDto
            {
                Success = false,
                Output = ex.Message
            });
        }
    }

    private List<string> ValidateCSharpCode(string code)
    {
        var errors = new List<string>();

        try
        {
            var syntaxTree = CSharpSyntaxTree.ParseText(code);
            var compilation = CSharpCompilation.Create(
                "Validation",
                new[] { syntaxTree },
                new[]
                {
                    MetadataReference.CreateFromFile(typeof(object).Assembly.Location),
                    MetadataReference.CreateFromFile(typeof(Console).Assembly.Location)
                });

            var diagnostics = compilation.GetDiagnostics();
            errors.AddRange(diagnostics
                .Where(d => d.Severity == DiagnosticSeverity.Error)
                .Select(d => d.GetMessage()));
        }
        catch (Exception ex)
        {
            errors.Add($"Compilation error: {ex.Message}");
        }

        return errors;
    }

    private List<string> ValidatePythonCode(string code)
    {
        var warnings = new List<string>();

        // 기본 Python 문법 검사 (간단한 체크)
        if (code.Contains("import os") || code.Contains("import sys"))
        {
            warnings.Add("Using system modules may be restricted in production");
        }

        if (code.Contains("eval(") || code.Contains("exec("))
        {
            warnings.Add("Using eval() or exec() is dangerous and may be blocked");
        }

        return warnings;
    }

    private List<string> ValidateJavaScriptCode(string code)
    {
        var warnings = new List<string>();

        // 기본 JavaScript 문법 검사
        if (code.Contains("eval(") || code.Contains("Function("))
        {
            warnings.Add("Using eval() or Function() constructor is dangerous and may be blocked");
        }

        if (code.Contains("require(") && !code.Contains("const fs"))
        {
            warnings.Add("Some Node.js modules may not be available");
        }

        return warnings;
    }
}

public class CompileCodeRequestDto
{
    public string Language { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
}

public class CompileResultDto
{
    public bool Success { get; set; }
    public List<string> Errors { get; set; } = new();
}

public class ValidateCodeRequestDto
{
    public string Language { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
}

public class ValidateResultDto
{
    public bool Valid { get; set; }
    public List<string> Errors { get; set; } = new();
    public List<string> Warnings { get; set; } = new();
}

public class TestCodeRequestDto
{
    public string Language { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
    public string? InputData { get; set; }
}

public class TestResultDto
{
    public bool Success { get; set; }
    public string Output { get; set; } = string.Empty;
}

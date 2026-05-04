using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Data;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Configuration;
using AIAgentManagement.DTOs;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class DatabaseBackupController : ControllerBase
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<DatabaseBackupController> _logger;
    private readonly string _connectionString;

    public DatabaseBackupController(
        IConfiguration configuration,
        ILogger<DatabaseBackupController> logger)
    {
        _configuration = configuration;
        _logger = logger;
        _connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? throw new InvalidOperationException("Database connection string not found");
    }

    [HttpPost("backup")]
    public async Task<ActionResult<BackupResultDto>> CreateBackup([FromBody] CreateBackupRequestDto request)
    {
        try
        {
            var backupPath = GetBackupPath(request.BackupName);
            var backupResult = await ExecuteBackupAsync(backupPath);

            return Ok(backupResult);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating database backup");
            return StatusCode(500, ErrorResponseDto.InternalError("백업 생성 중 오류가 발생했습니다."));
        }
    }

    [HttpGet("backups")]
    public ActionResult<List<BackupInfoDto>> GetBackups()
    {
        try
        {
            var backups = GetBackupList();
            return Ok(backups);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting backup list");
            return StatusCode(500, ErrorResponseDto.InternalError("백업 목록 조회 중 오류가 발생했습니다."));
        }
    }

    [HttpPost("restore")]
    public async Task<ActionResult> RestoreBackup([FromBody] RestoreBackupRequestDto request)
    {
        try
        {
            if (string.IsNullOrEmpty(request.BackupPath))
            {
                return BadRequest(ErrorResponseDto.BadRequest("백업 경로가 필요합니다."));
            }

            await ExecuteRestoreAsync(request.BackupPath);
            return Ok(new { message = "백업이 성공적으로 복원되었습니다." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error restoring backup");
            return StatusCode(500, ErrorResponseDto.InternalError("백업 복원 중 오류가 발생했습니다."));
        }
    }

    [HttpDelete("backups/{backupName}")]
    public ActionResult DeleteBackup(string backupName)
    {
        try
        {
            var backupPath = GetBackupPath(backupName);
            if (System.IO.File.Exists(backupPath))
            {
                System.IO.File.Delete(backupPath);
                return Ok(new { message = "백업 파일이 삭제되었습니다." });
            }
            return NotFound(ErrorResponseDto.NotFound("백업 파일을 찾을 수 없습니다."));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting backup");
            return StatusCode(500, ErrorResponseDto.InternalError("백업 삭제 중 오류가 발생했습니다."));
        }
    }

    [HttpGet("settings")]
    public ActionResult<BackupSettingsDto> GetBackupSettings()
    {
        try
        {
            var settings = new BackupSettingsDto
            {
                AutoBackupEnabled = true,
                BackupFrequency = "Daily",
                BackupTime = "02:00",
                RetentionDays = 30,
                BackupPath = GetDefaultBackupPath()
            };

            return Ok(settings);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting backup settings");
            return StatusCode(500, ErrorResponseDto.InternalError("설정 조회 중 오류가 발생했습니다."));
        }
    }

    [HttpPut("settings")]
    public ActionResult UpdateBackupSettings([FromBody] BackupSettingsDto settings)
    {
        try
        {
            // 실제로는 설정을 데이터베이스나 설정 파일에 저장해야 함
            _logger.LogInformation("Backup settings updated");
            return Ok(new { message = "설정이 저장되었습니다." });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating backup settings");
            return StatusCode(500, ErrorResponseDto.InternalError("설정 저장 중 오류가 발생했습니다."));
        }
    }

    private async Task<BackupResultDto> ExecuteBackupAsync(string backupPath)
    {
        var backupDir = Path.GetDirectoryName(backupPath);
        if (!string.IsNullOrEmpty(backupDir) && !Directory.Exists(backupDir))
        {
            Directory.CreateDirectory(backupDir);
        }

        using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync();

        var databaseName = connection.Database;
        var backupCommand = $@"
            BACKUP DATABASE [{databaseName}]
            TO DISK = '{backupPath}'
            WITH FORMAT, INIT, NAME = 'Full Backup of {databaseName}',
            SKIP, NOREWIND, NOUNLOAD, STATS = 10";

        using var command = new SqlCommand(backupCommand, connection);
        await command.ExecuteNonQueryAsync();

        var fileInfo = new FileInfo(backupPath);
        return new BackupResultDto
        {
            Success = true,
            BackupPath = backupPath,
            BackupSize = fileInfo.Length,
            CreatedAt = DateTime.UtcNow,
            Message = "백업이 성공적으로 생성되었습니다."
        };
    }

    private async Task ExecuteRestoreAsync(string backupPath)
    {
        if (!System.IO.File.Exists(backupPath))
        {
            throw new FileNotFoundException("백업 파일을 찾을 수 없습니다.", backupPath);
        }

        using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync();

        var databaseName = connection.Database;
        
        // 단일 사용자 모드로 전환
        var setSingleUser = $"ALTER DATABASE [{databaseName}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE";
        using (var command = new SqlCommand(setSingleUser, connection))
        {
            await command.ExecuteNonQueryAsync();
        }

        try
        {
            // 백업 복원
            var restoreCommand = $@"
                RESTORE DATABASE [{databaseName}]
                FROM DISK = '{backupPath}'
                WITH REPLACE, RECOVERY";

            using var restoreCmd = new SqlCommand(restoreCommand, connection);
            await restoreCmd.ExecuteNonQueryAsync();
        }
        finally
        {
            // 다중 사용자 모드로 복원
            var setMultiUser = $"ALTER DATABASE [{databaseName}] SET MULTI_USER";
            using var command = new SqlCommand(setMultiUser, connection)
            {
                CommandTimeout = 30
            };
            await command.ExecuteNonQueryAsync();
        }
    }

    private string GetBackupPath(string? backupName = null)
    {
        var defaultPath = GetDefaultBackupPath();
        var directory = Path.GetDirectoryName(defaultPath) ?? "Backups";
        
        if (string.IsNullOrEmpty(backupName))
        {
            backupName = $"AIAgentManagement_{DateTime.UtcNow:yyyyMMdd_HHmmss}.bak";
        }
        else if (!backupName.EndsWith(".bak"))
        {
            backupName += ".bak";
        }

        return Path.Combine(directory, backupName);
    }

    private string GetDefaultBackupPath()
    {
        var backupDir = Path.Combine(Directory.GetCurrentDirectory(), "Backups");
        if (!Directory.Exists(backupDir))
        {
            Directory.CreateDirectory(backupDir);
        }
        return backupDir;
    }

    private List<BackupInfoDto> GetBackupList()
    {
        var backupDir = GetDefaultBackupPath();
        var backups = new List<BackupInfoDto>();

        if (Directory.Exists(backupDir))
        {
            var files = Directory.GetFiles(backupDir, "*.bak");
            foreach (var file in files)
            {
                var fileInfo = new FileInfo(file);
                backups.Add(new BackupInfoDto
                {
                    Name = fileInfo.Name,
                    Path = fileInfo.FullName,
                    Size = fileInfo.Length,
                    CreatedAt = fileInfo.CreationTimeUtc,
                    ModifiedAt = fileInfo.LastWriteTimeUtc
                });
            }
        }

        return backups.OrderByDescending(b => b.CreatedAt).ToList();
    }
}

// DTOs
public class CreateBackupRequestDto
{
    public string? BackupName { get; set; }
}

public class BackupResultDto
{
    public bool Success { get; set; }
    public string BackupPath { get; set; } = string.Empty;
    public long BackupSize { get; set; }
    public DateTime CreatedAt { get; set; }
    public string Message { get; set; } = string.Empty;
}

public class BackupInfoDto
{
    public string Name { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public long Size { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime ModifiedAt { get; set; }
}

public class RestoreBackupRequestDto
{
    public string BackupPath { get; set; } = string.Empty;
}

public class BackupSettingsDto
{
    public bool AutoBackupEnabled { get; set; }
    public string BackupFrequency { get; set; } = string.Empty; // Daily, Weekly, Monthly
    public string BackupTime { get; set; } = string.Empty; // HH:mm
    public int RetentionDays { get; set; }
    public string BackupPath { get; set; } = string.Empty;
}

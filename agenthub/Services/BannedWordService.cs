using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;

namespace AIAgentManagement.Services;

public class BannedWordService : IBannedWordService
{
    private readonly AIAgentManagementDbContext _context;
    private readonly ILogger<BannedWordService> _logger;
    private readonly IMemoryCache _cache;
    private const string CACHE_KEY_GLOBAL = "BannedWords:Global";
    private const string CACHE_KEY_AGENT_PREFIX = "BannedWords:Agent:";
    private static readonly TimeSpan CacheExpiration = TimeSpan.FromMinutes(5);

    public BannedWordService(
        AIAgentManagementDbContext context,
        ILogger<BannedWordService> logger,
        IMemoryCache cache)
    {
        _context = context;
        _logger = logger;
        _cache = cache;
    }

    public async Task<BannedWordCheckResult> CheckBannedWordsAsync(string message, int? agentId)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            return new BannedWordCheckResult { IsBlocked = false };
        }

        try
        {
            var messageLower = message.ToLowerInvariant();
            var blockedWords = new List<string>();

            // 전역 금칙어 조회 (캐시 사용)
            var globalBannedWords = await GetGlobalBannedWordsCachedAsync();

            // Agent별 금칙어 조회 (캐시 사용)
            var agentBannedWords = new List<string>();
            if (agentId.HasValue)
            {
                agentBannedWords = await GetAgentBannedWordsCachedAsync(agentId.Value);
            }

            // 모든 금칙어 통합
            var allBannedWords = globalBannedWords.Concat(agentBannedWords).Distinct().ToList();

            // 메시지에서 금칙어 검사 (대소문자 구분 없이 부분 일치)
            foreach (var bannedWord in allBannedWords)
            {
                if (messageLower.Contains(bannedWord.ToLowerInvariant()))
                {
                    blockedWords.Add(bannedWord);
                }
            }

            return new BannedWordCheckResult
            {
                IsBlocked = blockedWords.Count > 0,
                BlockedWords = blockedWords
            };
        }
        catch (Exception ex)
        {
            // 테이블이 없을 경우 차단하지 않음
            if (ex.Message.Contains("Invalid object name") || ex.Message.Contains("does not exist"))
            {
                _logger.LogWarning("BannedWords table does not exist. Skipping banned word check. Please run CreateBannedWordsTable.sql");
                return new BannedWordCheckResult { IsBlocked = false };
            }
            _logger.LogError(ex, "Error checking banned words. Message: {Message}, AgentId: {AgentId}", message, agentId);
            // 에러 발생 시 차단하지 않음 (서비스 중단 방지)
            return new BannedWordCheckResult { IsBlocked = false };
        }
    }

    private async Task<List<string>> GetGlobalBannedWordsCachedAsync()
    {
        if (_cache.TryGetValue(CACHE_KEY_GLOBAL, out List<string>? cachedWords) && cachedWords != null)
        {
            return cachedWords;
        }

        var words = await _context.BannedWords
            .Where(bw => bw.AgentId == null && bw.IsActive)
            .Select(bw => bw.Word)
            .ToListAsync();

        _cache.Set(CACHE_KEY_GLOBAL, words, CacheExpiration);
        return words;
    }

    private async Task<List<string>> GetAgentBannedWordsCachedAsync(int agentId)
    {
        var cacheKey = CACHE_KEY_AGENT_PREFIX + agentId;
        if (_cache.TryGetValue(cacheKey, out List<string>? cachedWords) && cachedWords != null)
        {
            return cachedWords;
        }

        var words = await _context.BannedWords
            .Where(bw => bw.AgentId == agentId && bw.IsActive)
            .Select(bw => bw.Word)
            .ToListAsync();

        _cache.Set(cacheKey, words, CacheExpiration);
        return words;
    }

    public void InvalidateCache()
    {
        _cache.Remove(CACHE_KEY_GLOBAL);
        // Agent별 캐시는 키 패턴으로 삭제할 수 없으므로, 필요시 개별 삭제
        // 또는 캐시 만료 시간에 의존
    }

    public async Task<(List<BannedWordDto> Items, int TotalCount)> GetBannedWordsAsync(int? agentId, int page = 1, int pageSize = 20)
    {
        try
        {
            // 기본 쿼리 (변경 추적 비활성화로 성능 향상)
            var baseQuery = _context.BannedWords
                .AsNoTracking()
                .AsQueryable();

            if (agentId.HasValue)
            {
                baseQuery = baseQuery.Where(bw => bw.AgentId == agentId.Value);
            }
            else
            {
                // agentId가 null이면 전역 금칙어만 조회
                baseQuery = baseQuery.Where(bw => bw.AgentId == null);
            }

            // 전체 개수 조회 (인덱스 활용)
            var totalCount = await baseQuery.CountAsync();

            // 페이징 및 프로젝션을 쿼리 레벨에서 수행 (필요한 데이터만 조회)
            // 명시적 조인을 사용하여 성능 최적화
            var items = await (from bw in baseQuery
                              join agent in _context.Agents on bw.AgentId equals agent.AgentId into agentGroup
                              from agent in agentGroup.DefaultIfEmpty()
                              join creator in _context.Users on bw.CreatedBy equals creator.UserId
                              orderby bw.CreatedAt descending
                              select new BannedWordDto
                              {
                                  BannedWordId = bw.BannedWordId,
                                  Word = bw.Word,
                                  AgentId = bw.AgentId,
                                  AgentName = agent != null ? agent.AgentName : null,
                                  Description = bw.Description,
                                  IsActive = bw.IsActive,
                                  CreatedBy = bw.CreatedBy,
                                  CreatedByName = creator.FullName ?? creator.Email,
                                  CreatedAt = bw.CreatedAt,
                                  UpdatedAt = bw.UpdatedAt
                              })
                .Skip((page - 1) * pageSize)
                .Take(pageSize)
                .ToListAsync();

            return (items, totalCount);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting banned words. AgentId: {AgentId}, Page: {Page}, PageSize: {PageSize}. Error: {Error}", agentId, page, pageSize, ex.Message);
            // 테이블이 없을 경우 빈 리스트 반환
            if (ex.Message.Contains("Invalid object name") || ex.Message.Contains("does not exist"))
            {
                _logger.LogWarning("BannedWords table does not exist. Please run the migration script: CreateBannedWordsTable.sql");
                return (new List<BannedWordDto>(), 0);
            }
            throw;
        }
    }

    public async Task<BannedWordDto> CreateBannedWordAsync(CreateBannedWordRequestDto request, int userId)
    {
        var bannedWord = new BannedWord
        {
            Word = request.Word.Trim(),
            AgentId = request.AgentId,
            Description = request.Description?.Trim(),
            IsActive = true,
            CreatedBy = userId,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.BannedWords.Add(bannedWord);
        await _context.SaveChangesAsync();

        // 캐시 무효화
        InvalidateCache();

        _logger.LogInformation("금칙어 생성: BannedWordId={BannedWordId}, Word={Word}, AgentId={AgentId}, CreatedBy={CreatedBy}",
            bannedWord.BannedWordId, bannedWord.Word, bannedWord.AgentId, userId);

        return await MapToDtoAsync(bannedWord);
    }

    public async Task<BannedWordDto?> UpdateBannedWordAsync(int id, UpdateBannedWordRequestDto request, int userId)
    {
        var bannedWord = await _context.BannedWords
            .FirstOrDefaultAsync(bw => bw.BannedWordId == id);

        if (bannedWord == null)
            return null;

        if (!string.IsNullOrWhiteSpace(request.Word))
            bannedWord.Word = request.Word.Trim();

        if (request.AgentId.HasValue)
            bannedWord.AgentId = request.AgentId.Value;
        else if (request.AgentId == null && bannedWord.AgentId.HasValue)
            bannedWord.AgentId = null; // 전역으로 변경

        if (request.Description != null)
            bannedWord.Description = request.Description.Trim();

        if (request.IsActive.HasValue)
            bannedWord.IsActive = request.IsActive.Value;

        bannedWord.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();

        // 캐시 무효화
        InvalidateCache();

        _logger.LogInformation("금칙어 수정: BannedWordId={BannedWordId}, UpdatedBy={UpdatedBy}", id, userId);

        return await MapToDtoAsync(bannedWord);
    }

    public async Task<bool> DeleteBannedWordAsync(int id, int userId)
    {
        var bannedWord = await _context.BannedWords
            .FirstOrDefaultAsync(bw => bw.BannedWordId == id);

        if (bannedWord == null)
            return false;

        _context.BannedWords.Remove(bannedWord);
        await _context.SaveChangesAsync();

        // 캐시 무효화
        InvalidateCache();

        _logger.LogInformation("금칙어 삭제: BannedWordId={BannedWordId}, DeletedBy={DeletedBy}", id, userId);

        return true;
    }

    private async Task<BannedWordDto> MapToDtoAsync(BannedWord bannedWord)
    {
        await _context.Entry(bannedWord)
            .Reference(bw => bw.Agent)
            .LoadAsync();

        await _context.Entry(bannedWord)
            .Reference(bw => bw.Creator)
            .LoadAsync();

        return new BannedWordDto
        {
            BannedWordId = bannedWord.BannedWordId,
            Word = bannedWord.Word,
            AgentId = bannedWord.AgentId,
            AgentName = bannedWord.Agent?.AgentName,
            Description = bannedWord.Description,
            IsActive = bannedWord.IsActive,
            CreatedBy = bannedWord.CreatedBy,
            CreatedByName = bannedWord.Creator?.FullName ?? bannedWord.Creator?.Email,
            CreatedAt = bannedWord.CreatedAt,
            UpdatedAt = bannedWord.UpdatedAt
        };
    }
}

using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    public partial class DropSelfKnowledgeBase : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "AgentDocuments",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "DocumentChunks",
                schema: "AIAgentManagement");

            migrationBuilder.DropTable(
                name: "KnowledgeBaseDocuments",
                schema: "AIAgentManagement");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "KnowledgeBaseDocuments",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    DocumentId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    UserId = table.Column<int>(type: "integer", nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    IndexedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsIndexed = table.Column<bool>(type: "boolean", nullable: false),
                    SourceId = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    SourceType = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    Title = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_KnowledgeBaseDocuments", x => x.DocumentId);
                    table.ForeignKey(
                        name: "FK_KnowledgeBaseDocuments_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Users",
                        principalColumn: "UserId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AgentDocuments",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    AgentDocumentId = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    AgentId = table.Column<int>(type: "integer", nullable: false),
                    DocumentId = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AgentDocuments", x => x.AgentDocumentId);
                    table.ForeignKey(
                        name: "FK_AgentDocuments_Agents_AgentId",
                        column: x => x.AgentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "Agents",
                        principalColumn: "AgentId",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_AgentDocuments_KnowledgeBaseDocuments_DocumentId",
                        column: x => x.DocumentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "KnowledgeBaseDocuments",
                        principalColumn: "DocumentId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "DocumentChunks",
                schema: "AIAgentManagement",
                columns: table => new
                {
                    ChunkId = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    DocumentId = table.Column<int>(type: "integer", nullable: false),
                    ChunkIndex = table.Column<int>(type: "integer", nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    Embedding = table.Column<string>(type: "text", nullable: true),
                    Metadata = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DocumentChunks", x => x.ChunkId);
                    table.ForeignKey(
                        name: "FK_DocumentChunks_KnowledgeBaseDocuments_DocumentId",
                        column: x => x.DocumentId,
                        principalSchema: "AIAgentManagement",
                        principalTable: "KnowledgeBaseDocuments",
                        principalColumn: "DocumentId",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_AgentDocuments_AgentId_DocumentId",
                schema: "AIAgentManagement",
                table: "AgentDocuments",
                columns: new[] { "AgentId", "DocumentId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_AgentDocuments_DocumentId",
                schema: "AIAgentManagement",
                table: "AgentDocuments",
                column: "DocumentId");

            migrationBuilder.CreateIndex(
                name: "IX_DocumentChunks_DocumentId",
                schema: "AIAgentManagement",
                table: "DocumentChunks",
                column: "DocumentId");

            migrationBuilder.CreateIndex(
                name: "IX_KnowledgeBaseDocuments_UserId",
                schema: "AIAgentManagement",
                table: "KnowledgeBaseDocuments",
                column: "UserId");
        }
    }
}

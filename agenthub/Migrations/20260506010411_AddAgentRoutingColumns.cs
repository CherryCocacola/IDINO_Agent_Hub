using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    public partial class AddAgentRoutingColumns : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ConsumerSystems",
                schema: "AIAgentManagement",
                table: "Agents",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "KnowledgeBaseRef",
                schema: "AIAgentManagement",
                table: "Agents",
                type: "character varying(100)",
                maxLength: 100,
                nullable: true);

            // 기본값을 ADR-2 (KnowledgeBaseSource="AgentHub") / ADR-1 (LlmRouting="External") 에 맞게 부여한다.
            // 기존 PG row 도 본 기본값으로 채워져 신규 컬럼이 의미 있는 값이 된다.
            migrationBuilder.AddColumn<string>(
                name: "KnowledgeBaseSource",
                schema: "AIAgentManagement",
                table: "Agents",
                type: "character varying(32)",
                maxLength: 32,
                nullable: false,
                defaultValue: "AgentHub");

            migrationBuilder.AddColumn<string>(
                name: "LlmRouting",
                schema: "AIAgentManagement",
                table: "Agents",
                type: "character varying(16)",
                maxLength: 16,
                nullable: false,
                defaultValue: "External");

            migrationBuilder.AddColumn<string>(
                name: "RoutingPolicyJson",
                schema: "AIAgentManagement",
                table: "Agents",
                type: "text",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ConsumerSystems",
                schema: "AIAgentManagement",
                table: "Agents");

            migrationBuilder.DropColumn(
                name: "KnowledgeBaseRef",
                schema: "AIAgentManagement",
                table: "Agents");

            migrationBuilder.DropColumn(
                name: "KnowledgeBaseSource",
                schema: "AIAgentManagement",
                table: "Agents");

            migrationBuilder.DropColumn(
                name: "LlmRouting",
                schema: "AIAgentManagement",
                table: "Agents");

            migrationBuilder.DropColumn(
                name: "RoutingPolicyJson",
                schema: "AIAgentManagement",
                table: "Agents");
        }
    }
}

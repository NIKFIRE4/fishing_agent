using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class AddUsersAndSelectedFishingSpots : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "users",
                columns: table => new
                {
                    id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    tg_id = table.Column<long>(type: "bigint", nullable: false),
                    username = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true),
                    first_name = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true),
                    last_name = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_users", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "selected_fishing_spots",
                columns: table => new
                {
                    id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    user_id = table.Column<int>(type: "integer", nullable: false),
                    spot_name = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                    spot_coordinates = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    fishing_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    user_query = table.Column<string>(type: "text", nullable: true),
                    user_coordinates = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    selected_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_selected_fishing_spots", x => x.id);
                    table.ForeignKey(
                        name: "FK_selected_fishing_spots_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_selected_fishing_spots_user_id",
                table: "selected_fishing_spots",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "IX_users_tg_id",
                table: "users",
                column: "tg_id",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "selected_fishing_spots");

            migrationBuilder.DropTable(
                name: "users");
        }
    }
}

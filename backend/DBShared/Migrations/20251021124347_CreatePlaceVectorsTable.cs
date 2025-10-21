using System.Collections.Generic;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class CreatePlaceVectorsTable : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_TgMessages_Regions_IdRegion",
                table: "TgMessages");

            migrationBuilder.RenameColumn(
                name: "IdRegion",
                table: "TgMessages",
                newName: "RegionIdRegions");

            migrationBuilder.RenameIndex(
                name: "IX_TgMessages_IdRegion",
                table: "TgMessages",
                newName: "IX_TgMessages_RegionIdRegions");

            migrationBuilder.AddColumn<List<string>>(
                name: "UserPreferences",
                table: "Places",
                type: "text[]",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "PlaceVectors",
                columns: table => new
                {
                    IdVector = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    NameEmbedding = table.Column<List<float>>(type: "jsonb", nullable: true),
                    PreferencesEmbedding = table.Column<List<float>>(type: "jsonb", nullable: true),
                    IdPlace = table.Column<int>(type: "integer", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PlaceVectors", x => x.IdVector);
                    table.ForeignKey(
                        name: "FK_PlaceVectors_Places_IdPlace",
                        column: x => x.IdPlace,
                        principalTable: "Places",
                        principalColumn: "IdPlace",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_PlaceVectors_IdPlace",
                table: "PlaceVectors",
                column: "IdPlace",
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_TgMessages_Regions_RegionIdRegions",
                table: "TgMessages",
                column: "RegionIdRegions",
                principalTable: "Regions",
                principalColumn: "IdRegions",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_TgMessages_Regions_RegionIdRegions",
                table: "TgMessages");

            migrationBuilder.DropTable(
                name: "PlaceVectors");

            migrationBuilder.DropColumn(
                name: "UserPreferences",
                table: "Places");

            migrationBuilder.RenameColumn(
                name: "RegionIdRegions",
                table: "TgMessages",
                newName: "IdRegion");

            migrationBuilder.RenameIndex(
                name: "IX_TgMessages_RegionIdRegions",
                table: "TgMessages",
                newName: "IX_TgMessages_IdRegion");

            migrationBuilder.AddForeignKey(
                name: "FK_TgMessages_Regions_IdRegion",
                table: "TgMessages",
                column: "IdRegion",
                principalTable: "Regions",
                principalColumn: "IdRegions",
                onDelete: ReferentialAction.Cascade);
        }
    }
}

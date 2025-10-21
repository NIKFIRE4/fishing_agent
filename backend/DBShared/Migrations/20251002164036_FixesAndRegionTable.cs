using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class FixesAndRegionTable : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceFish_FishType_FishTypeId",
                table: "FishingPlaceFish");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceFish_FishingPlaces_FishingPlaceId",
                table: "FishingPlaceFish");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_WaterTypeId",
                table: "FishingPlaceWater");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_WaterType_WaterTypeId",
                table: "FishingPlaceWater");

            migrationBuilder.DropForeignKey(
                name: "FK_TgPhotos_TgMessages_MessageId",
                table: "TgPhotos");

            migrationBuilder.RenameColumn(
                name: "Name",
                table: "WaterType",
                newName: "WaterName");

            migrationBuilder.RenameColumn(
                name: "Id",
                table: "WaterType",
                newName: "IdWaterType");

            migrationBuilder.RenameColumn(
                name: "MessageId",
                table: "TgPhotos",
                newName: "IdTgMessage");

            migrationBuilder.RenameColumn(
                name: "Id",
                table: "TgPhotos",
                newName: "IdTgPhotos");

            migrationBuilder.RenameIndex(
                name: "IX_TgPhotos_MessageId",
                table: "TgPhotos",
                newName: "IX_TgPhotos_IdTgMessage");

            migrationBuilder.RenameColumn(
                name: "СhannelUrl",
                table: "TgMessages",
                newName: "SourceUrl");

            migrationBuilder.RenameColumn(
                name: "Id",
                table: "TgMessages",
                newName: "IdTgMessage");

            migrationBuilder.RenameColumn(
                name: "Name",
                table: "FishType",
                newName: "FishName");

            migrationBuilder.RenameColumn(
                name: "Id",
                table: "FishType",
                newName: "IdFishType");

            migrationBuilder.RenameColumn(
                name: "WaterTypeId",
                table: "FishingPlaceWater",
                newName: "IdWaterType");

            migrationBuilder.RenameColumn(
                name: "FishingPlaceId",
                table: "FishingPlaceWater",
                newName: "IdFishingPlace");

            migrationBuilder.RenameIndex(
                name: "IX_FishingPlaceWater_WaterTypeId",
                table: "FishingPlaceWater",
                newName: "IX_FishingPlaceWater_IdWaterType");

            migrationBuilder.RenameColumn(
                name: "Name",
                table: "FishingPlaces",
                newName: "PlaceName");

            migrationBuilder.RenameColumn(
                name: "Id",
                table: "FishingPlaces",
                newName: "IdFishingPlace");

            migrationBuilder.RenameIndex(
                name: "IX_FishingPlaces_Id",
                table: "FishingPlaces",
                newName: "IX_FishingPlaces_IdFishingPlace");

            migrationBuilder.RenameColumn(
                name: "FishTypeId",
                table: "FishingPlaceFish",
                newName: "IdFishType");

            migrationBuilder.RenameColumn(
                name: "FishingPlaceId",
                table: "FishingPlaceFish",
                newName: "IdFishingPlace");

            migrationBuilder.RenameIndex(
                name: "IX_FishingPlaceFish_FishTypeId",
                table: "FishingPlaceFish",
                newName: "IX_FishingPlaceFish_IdFishType");

            migrationBuilder.AddColumn<int>(
                name: "IdRegion",
                table: "TgMessages",
                type: "integer",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "Regions",
                columns: table => new
                {
                    IdRegions = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    RegionName = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Regions", x => x.IdRegions);
                });

            migrationBuilder.CreateIndex(
                name: "IX_WaterType_WaterName",
                table: "WaterType",
                column: "WaterName",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_TgMessages_IdRegion",
                table: "TgMessages",
                column: "IdRegion");

            migrationBuilder.CreateIndex(
                name: "IX_FishType_FishName",
                table: "FishType",
                column: "FishName",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Regions_RegionName",
                table: "Regions",
                column: "RegionName",
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceFish_FishType_IdFishType",
                table: "FishingPlaceFish",
                column: "IdFishType",
                principalTable: "FishType",
                principalColumn: "IdFishType",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceFish_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceFish",
                column: "IdFishingPlace",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdWaterType",
                table: "FishingPlaceWater",
                column: "IdWaterType",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_WaterType_IdWaterType",
                table: "FishingPlaceWater",
                column: "IdWaterType",
                principalTable: "WaterType",
                principalColumn: "IdWaterType",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_TgMessages_Regions_IdRegion",
                table: "TgMessages",
                column: "IdRegion",
                principalTable: "Regions",
                principalColumn: "IdRegions",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_TgPhotos_TgMessages_IdTgMessage",
                table: "TgPhotos",
                column: "IdTgMessage",
                principalTable: "TgMessages",
                principalColumn: "IdTgMessage",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceFish_FishType_IdFishType",
                table: "FishingPlaceFish");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceFish_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceFish");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdWaterType",
                table: "FishingPlaceWater");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_WaterType_IdWaterType",
                table: "FishingPlaceWater");

            migrationBuilder.DropForeignKey(
                name: "FK_TgMessages_Regions_IdRegion",
                table: "TgMessages");

            migrationBuilder.DropForeignKey(
                name: "FK_TgPhotos_TgMessages_IdTgMessage",
                table: "TgPhotos");

            migrationBuilder.DropTable(
                name: "Regions");

            migrationBuilder.DropIndex(
                name: "IX_WaterType_WaterName",
                table: "WaterType");

            migrationBuilder.DropIndex(
                name: "IX_TgMessages_IdRegion",
                table: "TgMessages");

            migrationBuilder.DropIndex(
                name: "IX_FishType_FishName",
                table: "FishType");

            migrationBuilder.DropColumn(
                name: "IdRegion",
                table: "TgMessages");

            migrationBuilder.RenameColumn(
                name: "WaterName",
                table: "WaterType",
                newName: "Name");

            migrationBuilder.RenameColumn(
                name: "IdWaterType",
                table: "WaterType",
                newName: "Id");

            migrationBuilder.RenameColumn(
                name: "IdTgMessage",
                table: "TgPhotos",
                newName: "MessageId");

            migrationBuilder.RenameColumn(
                name: "IdTgPhotos",
                table: "TgPhotos",
                newName: "Id");

            migrationBuilder.RenameIndex(
                name: "IX_TgPhotos_IdTgMessage",
                table: "TgPhotos",
                newName: "IX_TgPhotos_MessageId");

            migrationBuilder.RenameColumn(
                name: "SourceUrl",
                table: "TgMessages",
                newName: "СhannelUrl");

            migrationBuilder.RenameColumn(
                name: "IdTgMessage",
                table: "TgMessages",
                newName: "Id");

            migrationBuilder.RenameColumn(
                name: "FishName",
                table: "FishType",
                newName: "Name");

            migrationBuilder.RenameColumn(
                name: "IdFishType",
                table: "FishType",
                newName: "Id");

            migrationBuilder.RenameColumn(
                name: "IdWaterType",
                table: "FishingPlaceWater",
                newName: "WaterTypeId");

            migrationBuilder.RenameColumn(
                name: "IdFishingPlace",
                table: "FishingPlaceWater",
                newName: "FishingPlaceId");

            migrationBuilder.RenameIndex(
                name: "IX_FishingPlaceWater_IdWaterType",
                table: "FishingPlaceWater",
                newName: "IX_FishingPlaceWater_WaterTypeId");

            migrationBuilder.RenameColumn(
                name: "PlaceName",
                table: "FishingPlaces",
                newName: "Name");

            migrationBuilder.RenameColumn(
                name: "IdFishingPlace",
                table: "FishingPlaces",
                newName: "Id");

            migrationBuilder.RenameIndex(
                name: "IX_FishingPlaces_IdFishingPlace",
                table: "FishingPlaces",
                newName: "IX_FishingPlaces_Id");

            migrationBuilder.RenameColumn(
                name: "IdFishType",
                table: "FishingPlaceFish",
                newName: "FishTypeId");

            migrationBuilder.RenameColumn(
                name: "IdFishingPlace",
                table: "FishingPlaceFish",
                newName: "FishingPlaceId");

            migrationBuilder.RenameIndex(
                name: "IX_FishingPlaceFish_IdFishType",
                table: "FishingPlaceFish",
                newName: "IX_FishingPlaceFish_FishTypeId");

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceFish_FishType_FishTypeId",
                table: "FishingPlaceFish",
                column: "FishTypeId",
                principalTable: "FishType",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceFish_FishingPlaces_FishingPlaceId",
                table: "FishingPlaceFish",
                column: "FishingPlaceId",
                principalTable: "FishingPlaces",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_WaterTypeId",
                table: "FishingPlaceWater",
                column: "WaterTypeId",
                principalTable: "FishingPlaces",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_WaterType_WaterTypeId",
                table: "FishingPlaceWater",
                column: "WaterTypeId",
                principalTable: "WaterType",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_TgPhotos_TgMessages_MessageId",
                table: "TgPhotos",
                column: "MessageId",
                principalTable: "TgMessages",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }
    }
}

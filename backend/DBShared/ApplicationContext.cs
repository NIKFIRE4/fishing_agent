using Microsoft.EntityFrameworkCore;

using DBShared.Models;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;
using System.Text.Json;

namespace DBShared
{
    public class ApplicationContext : DbContext
    {     
        public DbSet<TgMessages> TgMessages { get; set; }
        public DbSet<TgPhotos> TgPhotos { get; set; }
        public DbSet<Places> Places { get; set; }
        public DbSet<FishType> FishType { get; set; }
        public DbSet<WaterType> WaterType { get; set; }
        public DbSet<Regions> Regions { get; set; }
        public DbSet<PlaceVectors> PlaceVectors { get; set; }
        public DbSet<FishingPlaceFish> FishingPlaceFish { get; set; }
        public DbSet<FishingPlaceWater> FishingPlaceWater { get; set; }
        public DbSet<User> users { get; set; }
        public DbSet<SelectedSpot> selected_fishing_spots { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            var connectionString = Environment.GetEnvironmentVariable("DB_CONNECTION_STRING");
            if (string.IsNullOrEmpty(connectionString))
            {
                throw new InvalidOperationException($"Переменная окружения DB_CONNECTION_STRING не задана {connectionString}.");
            }

            optionsBuilder.UseNpgsql(connectionString);
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            var jsonSerializerOptions = new JsonSerializerOptions();
            var listFloatConverter = new ValueConverter<List<float>?, string>(
                v => JsonSerializer.Serialize(v, jsonSerializerOptions),
                v => JsonSerializer.Deserialize<List<float>>(v, jsonSerializerOptions) ?? new List<float>());

            modelBuilder.Entity<TgMessages>()
                .HasMany(m => m.Photos)
                .WithOne(p => p.Messages)
                .HasForeignKey(p => p.IdTgMessage)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Regions>()
                .HasMany(r => r.Messages)
                .WithOne(m => m.Region)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Places>()
                .HasMany(fp => fp.Messages)
                .WithOne(m => m.Place)
                .HasForeignKey(m => m.PlaceId)
                .OnDelete(DeleteBehavior.SetNull);

            modelBuilder.Entity<FishingPlaceFish>()
                .HasKey(fpf => new { fpf.IdFishingPlace, fpf.IdFishType });

            modelBuilder.Entity<FishingPlaceFish>()
                .HasOne(fpf => fpf.FishingPlace)
                .WithMany(fp => fp.FishingPlaceFishes)
                .HasForeignKey(fpf => fpf.IdFishingPlace);

            modelBuilder.Entity<FishingPlaceFish>()
                .HasOne(fpf => fpf.FishType)
                .WithMany(ft => ft.FishingPlaceFishes)
                .HasForeignKey(fpf => fpf.IdFishType);

            modelBuilder.Entity<FishingPlaceWater>()
                .HasKey(fpw => new { fpw.IdFishingPlace, fpw.IdWaterType });

            modelBuilder.Entity<FishingPlaceWater>()
                .HasOne(fpw => fpw.FishingPlaces)
                .WithMany(fp => fp.FishingPlaceWaters)
                .HasForeignKey(fpw => fpw.IdFishingPlace);

            modelBuilder.Entity<FishingPlaceWater>()
                .HasOne(fpw => fpw.WaterType)
                .WithMany(wt => wt.FishingPlaceWaters)
                .HasForeignKey(fpw => fpw.IdWaterType);

            modelBuilder.Entity<Places>()
                .HasOne(p => p.PlaceVectors)
                .WithOne(pv => pv.Place)
                .HasForeignKey<PlaceVectors>(pv => pv.IdPlace)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<TgMessages>()
                .HasIndex(m => m.MessageId)
                .IsUnique();

            modelBuilder.Entity<TgMessages>()
                .Property(m => m.IsProcessed)
                .HasDefaultValue(false);

            modelBuilder.Entity<FishType>()
                .HasIndex(ft => ft.FishName)
                .IsUnique();

            modelBuilder.Entity<WaterType>()
                .HasIndex(ft => ft.WaterName)
                .IsUnique();

            modelBuilder.Entity<Regions>()
                .HasIndex(m => m.RegionName)
                .IsUnique();

            modelBuilder.Entity<Places>()
                .HasIndex(m => m.IdPlace)
                .IsUnique();

            modelBuilder.Entity<PlaceVectors>()
                .Property(pv => pv.NameEmbedding)
                .HasConversion(listFloatConverter)
                .HasColumnType("jsonb");

            modelBuilder.Entity<PlaceVectors>()
                .Property(pv => pv.PreferencesEmbedding)
                .HasConversion(listFloatConverter)
                .HasColumnType("jsonb");

            modelBuilder.Entity<User>()
                .HasMany(u => u.selected_spots)
                .WithOne(s => s.user)
                .HasForeignKey(s => s.user_id)
                .OnDelete(DeleteBehavior.Cascade);


            modelBuilder.Entity<User>()
                .HasIndex(u => u.tg_id)
                .IsUnique();

            modelBuilder.Entity<SelectedSpot>()
                .Property(s => s.spot_name)
                .HasMaxLength(255);

            modelBuilder.Entity<SelectedSpot>()
                .Property(s => s.spot_coordinates)
                .HasMaxLength(100);

            modelBuilder.Entity<SelectedSpot>()
                .Property(s => s.user_coordinates)
                .HasMaxLength(100);
        }
    }
}

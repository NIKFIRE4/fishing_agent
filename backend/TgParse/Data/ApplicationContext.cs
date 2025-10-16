
using Microsoft.EntityFrameworkCore;
using TgParse.Models;

namespace TgParse.Data
{
    public class ApplicationContext : DbContext
    {
        public DbSet<TgMessages> TgMessages { get; set; }
        public DbSet<TgPhotos> TgPhotos { get; set; }
        public DbSet<Places> Places { get; set; }
        public DbSet<FishType> FishType { get; set; }
        public DbSet<WaterType> WaterType { get; set; }
        public DbSet<Regions> Regions { get; set; }

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
            modelBuilder.Entity<TgMessages>()
                .HasMany(m => m.Photos)
                .WithOne(p => p.Messages)
                .HasForeignKey(p => p.IdTgMessage)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Regions>()
                .HasMany(r => r.Messages)
                .WithOne(m => m.Region)
                .HasForeignKey(m => m.IdRegion)
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

            modelBuilder.Entity<TgMessages>()
                .HasIndex(m => m.MessageId)
                .IsUnique();

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
        }
    }
}

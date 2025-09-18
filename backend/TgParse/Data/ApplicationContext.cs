using Microsoft.EntityFrameworkCore;
using TgParse.Models;

namespace TgParse.Data
{    
    public class ApplicationContext : DbContext
    {
        public DbSet<TgMessages> TgMessages { get; set; }
        public DbSet<TgPhotos> TgPhotos { get; set; }
        public DbSet<FishingPlaces> FishingPlaces { get; set; }   
        public DbSet<FishType> FishType { get; set; }
        public DbSet<WaterType> WaterType { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            //var connectionString = "Host=localhost;Port=5432;Database=FishingAgent;Username=postgres;Password=1lomalsteklo";
            var connectionString = Environment.GetEnvironmentVariable("DB_CONNECTION_STRING")
            ?? "${DB_CONNECTION_STRING}"
            ;

            optionsBuilder.UseNpgsql(connectionString);
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<TgMessages>()
                .HasMany(m => m.Photos)
                .WithOne(p => p.Message)
                .HasForeignKey(p => p.MessageId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<FishingPlaces>()
                .HasMany(fp => fp.Messages)
                .WithOne(m => m.Place)
                .HasForeignKey(m => m.PlaceId)
                .OnDelete(DeleteBehavior.SetNull);

            modelBuilder.Entity<FishingPlaceFish>()
                .HasKey(fpf => new { fpf.FishingPlaceId, fpf.FishTypeId });

            modelBuilder.Entity<FishingPlaceFish>()
                .HasOne(fpf => fpf.FishingPlace)
                .WithMany(fp => fp.FishingPlaceFishes)
                .HasForeignKey(fpf => fpf.FishingPlaceId);

            modelBuilder.Entity<FishingPlaceFish>()
                .HasOne(fpf => fpf.FishType)
                .WithMany(ft => ft.FishingPlaceFishes)
                .HasForeignKey(fpf =>  fpf.FishTypeId);

            modelBuilder.Entity<FishingPlaceWater>()
                .HasKey(fpw => new { fpw.FishingPlaceId, fpw.WaterTypeId });

            modelBuilder.Entity<FishingPlaceWater>()
                .HasOne(fpw => fpw.FishingPlaces)
                .WithMany(fp => fp.FishingPlaceWaters)
                .HasForeignKey(fpw => fpw.WaterTypeId);

            modelBuilder.Entity<FishingPlaceWater>()
                .HasOne(fpw => fpw.WaterType)
                .WithMany(wt => wt.FishingPlaceWaters)
                .HasForeignKey(fpw => fpw.WaterTypeId);

            modelBuilder.Entity<TgMessages>()
                .HasIndex(m => m.MessageId)
                .IsUnique();

            modelBuilder.Entity<FishingPlaces>()
                .HasIndex(m => m.Id)
                .IsUnique();
        }
    }
}

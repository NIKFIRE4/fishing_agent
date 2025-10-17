using System.ComponentModel.DataAnnotations;

namespace DBShared.Models
{
    public class FishType
    {
        [Key]
        public int IdFishType { get; set; }
        public string? FishName { get; set; }
        public List<FishingPlaceFish> FishingPlaceFishes { get; set; } = new List<FishingPlaceFish>();
    }
}

namespace TgParse.Models
{
    public class FishType
    {
        public int Id { get; set; }
        public string? Name { get; set; }
        public List<FishingPlaceFish> FishingPlaceFishes { get; set; } = new List<FishingPlaceFish>();
    }
}

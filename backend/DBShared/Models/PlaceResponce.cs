using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Text.Json.Serialization;

namespace DBShared.Models
{
    public class PlaceResponse
    {
        [JsonPropertyName("new_place")]
        public bool NewPlace { get; set; }

        [JsonPropertyName("name_location")]
        public string? NameLocation { get; set; }

        [JsonPropertyName("name_embedding")]
        public List<float>? NameEmbedding { get; set; }

        [JsonPropertyName("type_of_relax")]
        public string? TypeOfRelax { get; set; }

        [JsonPropertyName("user_preferences")]
        public List<string>? UserPreferences { get; set; }

        [JsonPropertyName("preferences_embedding")]
        public List<float>? PreferencesEmbedding { get; set; }

        [JsonPropertyName("place_coordinates")]
        public List<decimal>? PlaceCoordinates { get; set; }

        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("caught_fishes")]
        public List<string>? CaughtFishes { get; set; }

        [JsonPropertyName("water_space")]
        public List<string>? WaterSpace { get; set; }
    }
}

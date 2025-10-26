using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace DBShared.Models
{
    public class PlaceDtoBot : PlaceDto
    {
        [JsonPropertyName("place_id")]
        public int PlaceId { get; set; }

        [JsonPropertyName("vector_id")]
        public int IdVector { get; set; }

        [JsonPropertyName("name_embedding")]
        public List<float>? NameEmbedding { get; set; }

        [JsonPropertyName("preferences_embedding")]
        public List<float>? PreferencesEmbedding { get; set; }

        [JsonPropertyName("url_photos")]
        public List<string>? PhotosUrl { get; set; } = null;
    }
}

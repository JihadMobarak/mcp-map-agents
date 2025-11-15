# Reflection

**Lessons Learned**  
This project taught me to define each map action clearly and handle it the same way every time. Instead of writing quick one-off code, I described tools with clear inputs and outputs, which made routing questions (geocoding, routes, “nearby” places) much easier. I also learned to respect real-world limits: set a custom User-Agent for Nominatim, keep requests gentle, and keep Overpass queries small with a sensible radius. For routing, I now use the A→B endpoint for distance/time and make sure units are correct (meters→km, seconds→minutes). I also trimmed the chat history and summarized large results to avoid context-length errors.

**Potential Next Steps**  
I’d add caching and simple retries, plus fallback providers in case one service is slow or rate-limited. I want a small library of “POI presets” (cafes, hospitals, pharmacies) and to sort results by distance and basic quality. Running OSRM locally in Docker would make results faster and more consistent. I’d also add basic logging, a few more tests, and maybe a tiny web map so people can see the route or nearby places, while keeping the CLI for quick checks.

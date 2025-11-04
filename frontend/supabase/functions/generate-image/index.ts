import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { prompt, seed, steps, sampler } = await req.json();

    if (!prompt) {
      return new Response(
        JSON.stringify({ error: "Prompt is required" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    console.log("Generating image with params:", { prompt, seed, steps, sampler });

    // For now, return a placeholder - this will be integrated with your inference system
    // You can replace this with your actual ComfyUI API call or other inference service
    const mockImageUrl = `https://placehold.co/1024x1024/1a1a2e/ffffff?text=${encodeURIComponent(
      "Generated Image"
    )}`;

    return new Response(
      JSON.stringify({
        imageUrl: mockImageUrl,
        parameters: {
          prompt,
          seed: seed || "random",
          steps,
          sampler,
        },
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Error in generate-image function:", error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : "Unknown error" }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});

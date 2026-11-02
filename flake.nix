{
  description = "MCP server for Prowlarr: search indexers and queue downloads.";

  inputs = {
    flake-lib.url = "github:jgus-org/flake-lib/v1";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    {
      self,
      flake-lib,
      nixpkgs,
    }:
    flake-lib.lib.mkPythonFlake {
      inherit nixpkgs self;
      payload.packages =
        {
          buildApplication,
          pkgs,
          python,
          ...
        }:
        {
          prowlarr-mcp = buildApplication {
            build-system = [ python.hatchling ];
            dependencies = with python; [
              mcp
              httpx
            ];
            meta = {
              description = "MCP server for Prowlarr: search indexers and queue downloads.";
              license = pkgs.lib.licenses.mit;
              mainProgram = "prowlarr-mcp";
            };
            pname = "prowlarr-mcp";
            pyproject = true;
            pythonImportsCheck = [ "prowlarr_mcp" ];
            src = ./.;
            version = "0.1.0";
          };
        };
    };
}

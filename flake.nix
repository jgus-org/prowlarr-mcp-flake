{
  description = "MCP server for Prowlarr: search indexers and queue downloads.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;

        prowlarr-mcp = python.pkgs.buildPythonApplication {
          pname = "prowlarr-mcp";
          version = "0.1.0";
          pyproject = true;
          src = ./.;
          build-system = [ python.pkgs.hatchling ];
          dependencies = with python.pkgs; [ mcp httpx ];
          pythonImportsCheck = [ "prowlarr_mcp" ];
          meta = {
            description = "MCP server for Prowlarr: search indexers and queue downloads.";
            mainProgram = "prowlarr-mcp";
            license = pkgs.lib.licenses.mit;
          };
        };
      in
      {
        packages = {
          inherit prowlarr-mcp;
          default = prowlarr-mcp;
        };
      });
}

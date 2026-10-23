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
    flake-lib.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;

        orgFormatting = flake-lib.lib.mkFormatting {
          inherit self system;
        };

        prowlarr-mcp = python.pkgs.buildPythonApplication {
          build-system = [ python.pkgs.hatchling ];
          dependencies = with python.pkgs; [
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
      in
      {
        checks.formatting = orgFormatting.check;
        formatter = orgFormatting.formatter;
        packages = {
          inherit prowlarr-mcp;
          default = prowlarr-mcp;
        };
      }
    );
}

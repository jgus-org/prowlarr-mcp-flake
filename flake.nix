{
  description = "MCP server for Prowlarr: search indexers and queue downloads.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-lib = {
      url = "github:jgus-org/flake-lib/v1";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-lib,
      treefmt-nix,
    }:
    flake-lib.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;

        treefmtEval = treefmt-nix.lib.evalModule pkgs {
          projectRootFile = "flake.nix";
          programs.nixfmt.enable = true;
        };

        prowlarr-mcp = python.pkgs.buildPythonApplication {
          pname = "prowlarr-mcp";
          version = "0.1.0";
          pyproject = true;
          src = ./.;
          build-system = [ python.pkgs.hatchling ];
          dependencies = with python.pkgs; [
            mcp
            httpx
          ];
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

        formatter = treefmtEval.config.build.wrapper;
        checks.formatting = treefmtEval.config.build.check self;
      }
    );
}

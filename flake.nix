# SPDX-License-Identifier: GPL-3.0-or-later
{
  description = "Bad Apple, reconstructed from memory: procedural silhouettes and synthesis";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  outputs = { self, nixpkgs }: let
    systems = [ "x86_64-linux" "aarch64-linux" ];
  in {
    devShells = nixpkgs.lib.genAttrs systems (system: let
      pkgs = import nixpkgs { inherit system; };
    in {
      default = pkgs.mkShell {
        packages = [ (pkgs.python3.withPackages (p: [ p.numpy p.pillow ])) pkgs.ffmpeg pkgs.git pkgs.gh ];
      };
    });
  };
}

import commonjs from "@rollup/plugin-commonjs";
import json from "@rollup/plugin-json";
import nodeResolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

function createConfig(input, outputFile) {
  return {
    input,
    output: {
      esModule: true,
      file: outputFile,
      format: "es",
      sourcemap: false,
    },
    plugins: [
      typescript(),
      nodeResolve({ preferBuiltins: true }),
      commonjs(),
      json(),
    ],
  };
}

export default [
  createConfig("src/changelog-on-pr.ts", "dist/index.js"),
];

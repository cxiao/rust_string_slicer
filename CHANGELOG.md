# Changelog

## [1.0.1](https://github.com/cxiao/rust_string_slicer/compare/v1.0.0...v1.0.1) (2023-12-24)


### Bug Fixes

* Look for string data in both read-only sections and segments ([cbbacb6](https://github.com/cxiao/rust_string_slicer/commit/cbbacb608e1b840617e03854834b37412ecdbddd))

## 1.0.0 (2023-10-08)


### Features

* Apply recovered strings and new RustStringSlice type to binary ([d67e2a7](https://github.com/cxiao/rust_string_slicer/commit/d67e2a78413cf12325fc80353e5e7cee417e1280))
* Define char array of correct length when using code-based heuristic ([05cab7e](https://github.com/cxiao/rust_string_slicer/commit/05cab7e41235d9657e8b84808b860ca633ef1f70))
* Move analysis to background threads ([1faed30](https://github.com/cxiao/rust_string_slicer/commit/1faed306eef2850d4945fe9b2e4e14b73431cff2))
* Recover string slices from readonly data ([6bf2b21](https://github.com/cxiao/rust_string_slicer/commit/6bf2b2123198a9b22b7d83c732d9829dad49ebf7))
* Recover strings using code cross references ([1d59ea2](https://github.com/cxiao/rust_string_slicer/commit/1d59ea29b375ca0d3ba588d54a091a300762910c))
* Return list of string slices from recovery function ([2e8b211](https://github.com/cxiao/rust_string_slicer/commit/2e8b211436c8018b0a1e03918bc1a4fe6af51d6f))
* Set up plugin and register plugin action ([55151a7](https://github.com/cxiao/rust_string_slicer/commit/55151a79fcf6210903fcdda8fa01841f7a4350d9))

# Changelog

## [1.1.1](https://github.com/cxiao/rust_string_slicer/compare/v1.1.0...v1.1.1) (2026-01-11)


### Bug Fixes

* Fix broken type existence check after rename of RustStringSlice to &str ([28fec02](https://github.com/cxiao/rust_string_slicer/commit/28fec020f1d27aa44ac264950c61cfa8239713bd))

## [1.1.0](https://github.com/cxiao/rust_string_slicer/compare/v1.0.3...v1.1.0) (2026-01-11)


### Features

* Add underscore in front of field names ([24054c6](https://github.com/cxiao/rust_string_slicer/commit/24054c6df0d8861337c88b9b5727a0c233df967c))
* Minor clarification to progress text ([0e1dfc4](https://github.com/cxiao/rust_string_slicer/commit/0e1dfc4b7b02012652d9098b0dacf281f1252d82))
* Rename "RustStringSlice" type to "&str" ([a221f91](https://github.com/cxiao/rust_string_slicer/commit/a221f912a36bcf48df4cbb137dd63a318000e6c4))

## [1.0.3](https://github.com/cxiao/rust_string_slicer/compare/v1.0.2...v1.0.3) (2023-12-25)


### Bug Fixes

* Supress messy debug logging when recovering strings from code ([ef54800](https://github.com/cxiao/rust_string_slicer/commit/ef54800ad08fd3e6129cc864d13433c056151547))

## [1.0.2](https://github.com/cxiao/rust_string_slicer/compare/v1.0.1...v1.0.2) (2023-12-25)


### Bug Fixes

* Add valid UTF-8 and length filtering when recovering strings from code ([3e4024c](https://github.com/cxiao/rust_string_slicer/commit/3e4024ce91a7850207a8b4555bd32843383d4b16))
* Check for existence of RustStringSlice type before creating it ([4813149](https://github.com/cxiao/rust_string_slicer/commit/4813149f05c5d9d1152d20c00e4f851278f19c2d))
* When reecovering strings from code, also look for string data in both read-only sections and segments ([5a278f6](https://github.com/cxiao/rust_string_slicer/commit/5a278f6a1c8ede03fa7c451189c51ded68431881))

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

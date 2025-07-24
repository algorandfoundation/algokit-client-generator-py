# Changelog

<!--next-version-placeholder-->

## v2.2.0 (2025-07-24)

### Feature

* Add support for generating a minimal client ([#76](https://github.com/algorandfoundation/algokit-client-generator-py/issues/76)) ([`8dbfa88`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/8dbfa889cb4cca3c3f3bebcb6905e8240734f052))

## v2.1.0 (2025-03-26)

### Feature

* Bump utils dependency to v4 ([`386539b`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/386539b0e2c5fb6111b2d7617230ccd2cc58cb12))

## v2.0.1 (2025-03-13)

### Fix

* Ensure close_out calls are generated in composer ([#54](https://github.com/algorandfoundation/algokit-client-generator-py/issues/54)) ([`c96d18a`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/c96d18aeb45780d8a0c23162198e297a0c8ed3d8))

## v2.0.0 (2025-02-18)

### Feature

* V2 - leveraging new AlgoKit interfaces and support for algokit-utils-py v3 ([#33](https://github.com/algorandfoundation/algokit-client-generator-py/issues/33)) ([`de55aae`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/de55aaeab9b45753723cfda55bbc058358749bd5))

### Fix

* Update to latest utils to fix state key name normalization issues similarly to utils-ts ([#43](https://github.com/algorandfoundation/algokit-client-generator-py/issues/43)) ([`f7f9078`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/f7f9078998c58a66bbd7adc23a3a132be55f9b48))
* Correcting the ignore declaration for a more appropriate mypy global ignore ([#41](https://github.com/algorandfoundation/algokit-client-generator-py/issues/41)) ([`83a3836`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/83a383699a9ccd15a72709825d3bd891f5236990))
* Disable mypy for end user; keep selective ignores for local examples ([#40](https://github.com/algorandfoundation/algokit-client-generator-py/issues/40)) ([`7755be2`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/7755be2708faec9e5cecf9cf04d7151d3ebcda7d))
* Minor patches in dataclass inheritance; fixes for mypy errors; addressing internal feedback ([#37](https://github.com/algorandfoundation/algokit-client-generator-py/issues/37)) ([`82a1a1c`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/82a1a1c304782877550d2f2ea137787b56b91015))
* Ensure nested dataclasses in state accessors are loaded properly ([#36](https://github.com/algorandfoundation/algokit-client-generator-py/issues/36)) ([`58f13aa`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/58f13aae382136fb4ce37f1b0c44717e5258d2d3))
* Extra section in migration for state access; adding @property decorator for direct state access ([#35](https://github.com/algorandfoundation/algokit-client-generator-py/issues/35)) ([`e8b49e5`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/e8b49e57de9cb27fc9ec18a93050929c63e574c4))

### Breaking

* Generator overhaul with ARC-56 support and TypeScript alignment ([`de55aae`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/de55aaeab9b45753723cfda55bbc058358749bd5))

### Documentation

* Patch typo; ignore cd on changes in docs folder only ([#42](https://github.com/algorandfoundation/algokit-client-generator-py/issues/42)) ([`0034c28`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/0034c283fd6597ecfb00a98fbaa9611feb610948))

## v1.1.7 (2024-08-08)



## v1.1.6 (2024-08-01)

### Fix

* Additional changes to address mypy 'call-overload'; adding cron for ci ([#29](https://github.com/algorandfoundation/algokit-client-generator-py/issues/29)) ([`d3a64f7`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/d3a64f78792d003520ab4283390571de9502ad23))
* Addressing mypy 'call-overload' warning with explicit typecast ([#28](https://github.com/algorandfoundation/algokit-client-generator-py/issues/28)) ([`ffa9f23`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/ffa9f23d072ed7fc354394a045bf7c2b9ce3a04a))

## v1.1.5 (2024-06-13)

### Fix

* Set explicit utf-8 encoding as part of writer invocation ([#27](https://github.com/algorandfoundation/algokit-client-generator-py/issues/27)) ([`002de46`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/002de46a4e1932b1bac45ffc90ca8f86129f6201))

## v1.1.4 (2024-05-13)

### Fix

* Ensure clients generated for contracts with no abi methods are still valid python ([`a3e1c8b`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/a3e1c8b88669cd148d51d3856afd2e9fdf8a8c9b))

## v1.1.3 (2024-03-27)



## v1.1.2 (2024-02-06)



## v1.1.1 (2024-01-08)



## v1.1.0 (2023-12-14)

### Feature

* Add support for simulating an atc ([#17](https://github.com/algorandfoundation/algokit-client-generator-py/issues/17)) ([`6135632`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/6135632ec18cd9ec8652838031afc05c1e84528e))

### Fix

* Adjust client tests ([#18](https://github.com/algorandfoundation/algokit-client-generator-py/issues/18)) ([`76d36b1`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/76d36b1dd414bac27c2d672d1534475b0181ac9b))

## v1.0.3 (2023-10-17)



## v1.0.2 (2023-06-23)

### Fix

* Fix account reference types ([#13](https://github.com/algorandfoundation/algokit-client-generator-py/issues/13)) ([`8cedcd9`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/8cedcd92cb81fa8be302940b195fe522be937c8a))

## v1.0.1 (2023-06-13)

### Fix

* Add support for reference type aliases ([#12](https://github.com/algorandfoundation/algokit-client-generator-py/issues/12)) ([`0d5a5d8`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/0d5a5d844f2594f0da29749e56d9a64ed0bfc2c6))

## v1.0.0 (2023-06-06)

### Fix

* Initial release ([`1cdd35a`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/1cdd35ac97560c9fe2c7e3fef7a0dd020fa093fd))
* Initial release ([#11](https://github.com/algorandfoundation/algokit-client-generator-py/issues/11)) ([`8519a98`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/8519a98387bed0cc28feaf7eb6d39d64204bba84))

### Breaking

* initial release ([`1cdd35a`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/1cdd35ac97560c9fe2c7e3fef7a0dd020fa093fd))

## v0.1.0 (2023-06-06)

### Feature

* Add compose functionality to generated clients ([#9](https://github.com/algorandfoundation/algokit-client-generator-py/issues/9)) ([`98b8d4d`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/98b8d4d8330fc5dbf2351407540f848b80008989))
* Add additional doc strings ([`b900d56`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/b900d56ffcee007c61361f63f3248b4a2952931c))
* Generate client method docstrings ([`a0f3ace`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/a0f3ace59f7630451ebc5360fc79387b2bc03b07))
* Expand supported types ([`5a23813`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/5a23813fd5105fc1ad900e4e729bca63ad7413bd))
* Forward commonly used properties ([`2b4873b`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/2b4873bc8ce374eaf1fa65d74cc42b90068d19f5))
* Support for named structs ([`d05e79b`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/d05e79bc1b8c993157e775d8edfa1723dcf3256e))
* Convert special methods from overloads to prefixed names ([`0aa67e6`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/0aa67e63404e000c7e6993a3595cd93b56999630))
* Improve CLI parsing robustness ([`046f88e`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/046f88e34dbf24cbf6adeac7e6857c9d6c007a28))
* Enable running as a CLI ([`7d12057`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/7d120573888a3066b51922e0e322be57a8514a2c))
* Add algokit typed client generator ([`1831730`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/1831730faae20b401c87e1e4c720875197476736))

### Fix

* Use logger instead of print ([`109bffb`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/109bffb6d44fff3288ecbf1f233228f3eb86ec24))
* Remove GenerationSettings ([`3340a39`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/3340a394ed8b7a40f72b34df5a4743a5fa34ade3))
* Reduce type warnings ([`b3f2e5e`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/b3f2e5ebf2a0cc9f2e7c19278cc7ea455d9bc03a))
* Use names derived from ABI signature if overloads ([`a9fec9c`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/a9fec9c2f00d24dbab4dceec7e6912a89747c0d7))
* Rename CLI alias to algokitgen-py ([`f968dd0`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/f968dd02dacc5846061e8935d3725258f4a60c85))
* Map byte[] to bytes ([#3](https://github.com/algorandfoundation/algokit-client-generator-py/issues/3)) ([`68bdee3`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/68bdee392dd811227e694c2f1aac0d57dde6ee0e))

### Documentation

* Update README.md ([`fb197c0`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/fb197c0a47fc3d6f82cb62c6a2be6c607bc636ad))
* Update README.md ([`d35a37b`](https://github.com/algorandfoundation/algokit-client-generator-py/commit/d35a37b9868ff14747395ca9ece6bd83fc476e37))

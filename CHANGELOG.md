# Changelog

## [1.0.1](https://github.com/oonamo/CMyReflection/compare/v1.0.0...v1.0.1) (2026-09-23)


### Bug Fixes

* **format-plugin:** align changelog path ([683f03e](https://github.com/oonamo/CMyReflection/commit/683f03ea0eef9ead58fb51ea5c3c11c2075471c7))
* **json-plugin:** align changelog path ([683f03e](https://github.com/oonamo/CMyReflection/commit/683f03ea0eef9ead58fb51ea5c3c11c2075471c7))
* resolve nested folder generation in release zip ([683f03e](https://github.com/oonamo/CMyReflection/commit/683f03ea0eef9ead58fb51ea5c3c11c2075471c7))

## [1.0.0](https://github.com/oonamo/CMyReflection/compare/v1.0.0...v1.0.0) (2026-09-23)


### ⚠ BREAKING CHANGES

* rename print plugin to format
* **json:** escape strings and unify write callbacks
* **parser:** require a --input flag, --plugin is now a list
* rename MetaData_FromName -> StructMetaData_FromName for consistency
* seperate structs and enums into seperate tags
* add Reflection class to type_mapper function handler
* change tags to be namespaced
* add basic plugin helpers, tests
* rename FieldInfo -> StructFieldInfo and similar functions for consistency
* rename *field_tags -> *struct_field_tags
* rename struct_name field to be more consistent
* rename field extension variables to be clearer
* use dataclasses for plugin creating rather then global instances
* data driven plugins
* add base type lookup
* add @length tag for specifying inline array lengths
* Use `ReflectResult` enum for error checking
* automatically add structs as typed fields, regardless if it's in

### BRREAKING

* **parser:** require a --input flag, --plugin is now a list ([9b9f836](https://github.com/oonamo/CMyReflection/commit/9b9f836d2f74569c6375a1c2dd31cac5381f55c7))


### Features

* `get_array_element` function for safely extracting members ([717c5e0](https://github.com/oonamo/CMyReflection/commit/717c5e08eb824c2911601da9d7b0436660e91097))
* add [@length](https://github.com/length) tag for specifying inline array lengths ([785a4c2](https://github.com/oonamo/CMyReflection/commit/785a4c242111d96e64704e5fbe5c15745520b67f))
* add `readonly` and `writeonly` tags ([9f1ea99](https://github.com/oonamo/CMyReflection/commit/9f1ea9970139f885f12a474171deb72c90c09653))
* add array lookups to reflection ([382d57b](https://github.com/oonamo/CMyReflection/commit/382d57bd2d102e093ebf6e5a7b035c590cd7ac6b))
* add base type lookup ([76a9896](https://github.com/oonamo/CMyReflection/commit/76a9896854c5d22262d1cbb8e5991727ff67dbe7))
* add basic plugin helpers, tests ([8f0c566](https://github.com/oonamo/CMyReflection/commit/8f0c566d8e5dd2b72256e917b1c856fc061ff57d))
* add better header formatting ([80f86c3](https://github.com/oonamo/CMyReflection/commit/80f86c34cb18833138e79bc9fbb5abd74e90eaee))
* add check method to CBuilder ([2f9f120](https://github.com/oonamo/CMyReflection/commit/2f9f120839230ded69415eee57038fcb96df0bc1))
* add cmake and make examples ([1164acd](https://github.com/oonamo/CMyReflection/commit/1164acd4b46eda3a773d81b7fb939fd1e0883860))
* add enforcement and validation for field types ([061e4bc](https://github.com/oonamo/CMyReflection/commit/061e4bce9c68e7f318c4bd25e1fa10c6e864f56c))
* add enum metadata macro ([c6341da](https://github.com/oonamo/CMyReflection/commit/c6341dacd32e50f47e494dd1cd480734f4fa9add))
* add get_type_size function ([b6f9ced](https://github.com/oonamo/CMyReflection/commit/b6f9ced50322d350b602f6cbf6a44fee71ef7a17))
* add getter functions with read length safety ([a5ea290](https://github.com/oonamo/CMyReflection/commit/a5ea290c2206b61bc3290ee96e089811842c4aa0))
* add git diagram ([726ee3f](https://github.com/oonamo/CMyReflection/commit/726ee3f1da599198f9a5388e6df5fcbde688c926))
* add guard clauses to switch type ([134e4bb](https://github.com/oonamo/CMyReflection/commit/134e4bbe51bd7fa9c1a1dca6d2f2b9e12dd7f7c8))
* add helper search macros ([de24675](https://github.com/oonamo/CMyReflection/commit/de2467539ba6f7b8e77bb5bd77af1461bea3dbf8))
* add json validation testing with node ([c52be19](https://github.com/oonamo/CMyReflection/commit/c52be19e151d2304e00cbbf6fcca53ee4fe259fa))
* add metadata generation macro ([c3ec843](https://github.com/oonamo/CMyReflection/commit/c3ec8432ec62ac2f4ed2df19fcc6c1b7db8e9b31))
* add metadata to parse script ([f6a4d8c](https://github.com/oonamo/CMyReflection/commit/f6a4d8c0c64cc0e6ca331a0becc0b03c8146531b))
* add reflect_query function ([0e018fd](https://github.com/oonamo/CMyReflection/commit/0e018fd83c3c6ab8319c4828bee19b87ee2f37f4))
* add Reflection class to type_mapper function handler ([e6eeb0f](https://github.com/oonamo/CMyReflection/commit/e6eeb0f7064f3a2500a2a3f08e89e83d144b54b8))
* add resolve_field_metadata function ([90de1e9](https://github.com/oonamo/CMyReflection/commit/90de1e98e6b7316dc84c84333ea4d468bd438047))
* add reverse lookup function for enums ([83cf22e](https://github.com/oonamo/CMyReflection/commit/83cf22ee29f8f85a81b0bd770da6070ea1831b92))
* add stricter warnings to all compiled tests and examples ([4a51b77](https://github.com/oonamo/CMyReflection/commit/4a51b77169ea7e7a5ec6dc62174f8fd48665dddd))
* add support for custom FieldType declartions ([d80b0b6](https://github.com/oonamo/CMyReflection/commit/d80b0b645230f8dc30b78912066720d7558747f4))
* add visitor pattern to reflection ([ccf1042](https://github.com/oonamo/CMyReflection/commit/ccf1042361f49ed6c368b89dae6ee80cb3b34740))
* allow for array defines ([e92bdf7](https://github.com/oonamo/CMyReflection/commit/e92bdf775fb72f1be5a22d2c2516e2413a1f6709))
* basic c code builder ([5971d94](https://github.com/oonamo/CMyReflection/commit/5971d943e66411327eae52418e2099d366204924))
* basic json serialization ([f121769](https://github.com/oonamo/CMyReflection/commit/f121769fc5d7f2bc193d958b46c607d15b0c9e9a))
* **cd:** add function for easily creating reflection metadata ([de65ef4](https://github.com/oonamo/CMyReflection/commit/de65ef4785cf1e08800be091187442f05d492f08))
* check for member safety in enums ([bc18797](https://github.com/oonamo/CMyReflection/commit/bc187973aa5e0630d4a28c733d6fb48a54d96b8e))
* compile with strict compiler warnings ([90e6ee2](https://github.com/oonamo/CMyReflection/commit/90e6ee29aa15d05444e7e8d0801659d3cc85ea1a))
* correctly generate EnumMemberExtension ([ed284e0](https://github.com/oonamo/CMyReflection/commit/ed284e0e978caa1faf36ddd0610ace13ae6b44f5))
* create plugin generator ([eae1211](https://github.com/oonamo/CMyReflection/commit/eae1211849e7e11f0e43b04d4af7aa2af9daf04f))
* **create_plugin:** check for existing file before overwriting ([90a3a2f](https://github.com/oonamo/CMyReflection/commit/90a3a2f01451bbaaa3354e4d16490b54748a1ccc))
* CVar builder class ([cee125a](https://github.com/oonamo/CMyReflection/commit/cee125ab509a0dce622a77ca7f588633ce68617b))
* data driven plugins ([cd0af2c](https://github.com/oonamo/CMyReflection/commit/cd0af2cfd8416e2af53de0b1409087cbde0f1723))
* dependency sorting, strict errors ([00990e0](https://github.com/oonamo/CMyReflection/commit/00990e009919635129832b22b884068076afe102))
* don't add stand alone function definition if it is marked extern ([0380618](https://github.com/oonamo/CMyReflection/commit/0380618b0a36f7746b6953f8d4c593f2b2aa7c51))
* dynamic array helpers ([119e181](https://github.com/oonamo/CMyReflection/commit/119e18129e8bed5c8953db33ce92429e1cbee97e))
* fix typo in header generator ([6514b88](https://github.com/oonamo/CMyReflection/commit/6514b883d20e385297c1c57bef900b6f7b431228))
* fix warnings, disable warnings on msvc ([ec02782](https://github.com/oonamo/CMyReflection/commit/ec02782b89cab59541470c99c89edd050dc2d8ce))
* function generation ([8c1f4b2](https://github.com/oonamo/CMyReflection/commit/8c1f4b28e8e6e15ba47c723f3e409290eeaeb843))
* get ready for initial release ([e93b5d6](https://github.com/oonamo/CMyReflection/commit/e93b5d6210b27b2bd8c10ab9e7dbc5ec77572065))
* implement function for getting names of the FieldTypes ([01f85d5](https://github.com/oonamo/CMyReflection/commit/01f85d5b23278d095a4907db8fc6345ed3f29553))
* initial json prototype ([f69b4c6](https://github.com/oonamo/CMyReflection/commit/f69b4c6285d27b05063c5badf04f5e75f2692d3e))
* initial plugin prototype ([627e899](https://github.com/oonamo/CMyReflection/commit/627e89993aeefda3bd89793b9c1351699ca0b5b4))
* **json:** add callback functions for flushing and resizing ([54079da](https://github.com/oonamo/CMyReflection/commit/54079dac38368fbba2365ea71c1a757beaf7890c))
* **json:** add debug information macro ([dbd4054](https://github.com/oonamo/CMyReflection/commit/dbd4054c49807a0c9edc8c98e1ebc3f46df1ccb5))
* **json:** add json_key_name for adding custom key names to struct fields ([ff7156a](https://github.com/oonamo/CMyReflection/commit/ff7156ae5dc6253463c0c4b240f8ee5df303e248))
* more helpers ([347ed0e](https://github.com/oonamo/CMyReflection/commit/347ed0eb7cef37a90a167f06b1f18ab803dd8381))
* **parser:** add doc comments to plugin relevant functions ([a3034e0](https://github.com/oonamo/CMyReflection/commit/a3034e053dde426a087a30f0c1bc8a76f11723c6))
* **plugins:** add pre_macro field for plugins ([70afa6a](https://github.com/oonamo/CMyReflection/commit/70afa6a3806676c1a7800ea80ea3d3bf888e04a6))
* primitive plugin system with print extension ([79ff8db](https://github.com/oonamo/CMyReflection/commit/79ff8db6f8e2fafa8c880e46029360257ab8abb5))
* **printer:** handle more primitive types ([365695e](https://github.com/oonamo/CMyReflection/commit/365695ee58d41d7badcf3165090a33ef55341414))
* **reflector:** strip spacing in function declarations ([62f69f6](https://github.com/oonamo/CMyReflection/commit/62f69f696cb1995af006e5df13195beee39e8042))
* seperate structs and enums into seperate tags ([e8828bc](https://github.com/oonamo/CMyReflection/commit/e8828bc492f547020a325b08a7d78fa421b07f12))
* show example json output ([025bb34](https://github.com/oonamo/CMyReflection/commit/025bb34f1590a01d07586f14ed0edbed6ad26c13))
* struct registry for lookups with recursive support ([3f844eb](https://github.com/oonamo/CMyReflection/commit/3f844eb026ca298d255867809d723705934f860b))
* support enum reflection ([43e0dab](https://github.com/oonamo/CMyReflection/commit/43e0dab25b074ed643e1a38168e2b88a22bd47e4))
* unit testing ([7dc183d](https://github.com/oonamo/CMyReflection/commit/7dc183d4e46cd46ad93af116ba57366e0aaec1cc))
* unit tests for printer plugin ([b48490e](https://github.com/oonamo/CMyReflection/commit/b48490e5e9d04b66290c94b3de390672610bfd56))
* update header documentation with more examples ([22f66a5](https://github.com/oonamo/CMyReflection/commit/22f66a585e488444d22bd427619e23ac4d35fbd3))
* update header formatting ([32cd2cd](https://github.com/oonamo/CMyReflection/commit/32cd2cd320b6259f0a19f58a26a96155b06a5378))
* update parser ([b90d919](https://github.com/oonamo/CMyReflection/commit/b90d919e6168c8284689eaaeef5d754357ffc383))
* update printer plugin to use builder pattern ([68d9468](https://github.com/oonamo/CMyReflection/commit/68d94686fc5ddbea91ca5937870d0cfe1cbcb65e))
* update printer plugin with serialization features ([dcc5c07](https://github.com/oonamo/CMyReflection/commit/dcc5c07442d14e794a2bc50f7727cfcbd327c7ed))
* Use `ReflectResult` enum for error checking ([a384d44](https://github.com/oonamo/CMyReflection/commit/a384d44b5f275fefd56d7d2e1e88297104e431d0))
* use dataclasses for plugin creating rather then global instances ([a1cc9f1](https://github.com/oonamo/CMyReflection/commit/a1cc9f148e78d8ca1b69be65e64bb2746dec6719))


### Bug Fixes

* add bounds checking to memory access functions ([5d96f4d](https://github.com/oonamo/CMyReflection/commit/5d96f4d16f806ce5452b1c8093f0f852174953df))
* add CMY_REFLECTION definition to generated file ([9c62312](https://github.com/oonamo/CMyReflection/commit/9c6231270b041bbaffcada5065387f21706b4673))
* add stddef.h to includes to fix undefined types ([9fd8e9f](https://github.com/oonamo/CMyReflection/commit/9fd8e9fda2d7ffb70edc3c98b396a4ec88474411))
* allow for white space in function signature regex ([0a1574d](https://github.com/oonamo/CMyReflection/commit/0a1574dd25014428c7a181184d29d265d6a22fc2))
* apply changes to generated files ([c7e5262](https://github.com/oonamo/CMyReflection/commit/c7e5262cd3c297ef808b86bc9b5b4425ad34fb90))
* automatically add structs as typed fields, regardless if it's in ([963b92d](https://github.com/oonamo/CMyReflection/commit/963b92d4011d017172491f65cad41b1a5e23a71a))
* cast all getter functions out values to void* to fix warnings ([ea2ac60](https://github.com/oonamo/CMyReflection/commit/ea2ac609220dd8c5b6870af35c2349332930c09c))
* change getters to include semicolon ([5971d94](https://github.com/oonamo/CMyReflection/commit/5971d943e66411327eae52418e2099d366204924))
* check for array type in template, remove type unknown from type mapping ([a98a78b](https://github.com/oonamo/CMyReflection/commit/a98a78b088e9625bc6ef6a2fd684baf653188ef9))
* check that filename exists in dict before overwriting ([4aabdcc](https://github.com/oonamo/CMyReflection/commit/4aabdcce402d96c6c0597cf33e91e3b879cedb1f))
* correctly add plugin ([e5d2b57](https://github.com/oonamo/CMyReflection/commit/e5d2b57f6dd0bba95007d1b18cf87437afa3d1e6))
* create function definitions even if no cases are defined ([63f2310](https://github.com/oonamo/CMyReflection/commit/63f231082dd304edc963859906b8f57ba190b95e))
* don't add function definition if it is extern ([70d95aa](https://github.com/oonamo/CMyReflection/commit/70d95aa738b093825127d7532fd7ed23a815335f))
* fix bug in parser script ([9c0d4d1](https://github.com/oonamo/CMyReflection/commit/9c0d4d1013e5b5d029dbb1561152324e77f546c3))
* fix corruption in adjacent fields ([d903413](https://github.com/oonamo/CMyReflection/commit/d9034137ff628da5f84548d7f83f126a9ced9286))
* fix nullptr dereference, sign conversivness, and include macro in header ([afc6227](https://github.com/oonamo/CMyReflection/commit/afc6227c433bdd3204bb059ab5c6244d3aa492b7))
* formatting in readme and example ([518f8de](https://github.com/oonamo/CMyReflection/commit/518f8deb563b9ad3cbc84db8c8ed91625c31f722))
* generate GET_EXT_* macros if field extensions is defined, indepedent of use ([86f1d8e](https://github.com/oonamo/CMyReflection/commit/86f1d8edd0d11c591fed96e30d574337f025df25))
* **json:** fix memory leak in test ([6089d4f](https://github.com/oonamo/CMyReflection/commit/6089d4fb3acee76d1e916fa34095d7f215b4e6ad))
* more consistent naming ([c839de5](https://github.com/oonamo/CMyReflection/commit/c839de5dc4df06a2b15de3fb62e9dde437de4c22))
* preproc macro to correctly check for windows ([9ceebd0](https://github.com/oonamo/CMyReflection/commit/9ceebd02a8972f1818fbd90085d99b8baa9a4350))
* prevent pedantic warning when not using parser ([94b358e](https://github.com/oonamo/CMyReflection/commit/94b358e6c6b2626592c7abe8363a855e989e6b6a))
* **printer:** change size of array to be of field-&gt;count, if in bounds ([23f7439](https://github.com/oonamo/CMyReflection/commit/23f743970ea1397afb2a2f36d33d79f84021a713))
* **printer:** use CMY_PRINTER_MAX_BUF_LEN for defining max buffer size ([599c409](https://github.com/oonamo/CMyReflection/commit/599c40958b199c9adbdb3a1307b2a4d53e745529))
* rename MetaData_FromName -&gt; StructMetaData_FromName for consistency ([442adcf](https://github.com/oonamo/CMyReflection/commit/442adcf1e9704f97aadbdd0162be98bbe1582f52))
* return REFLECT_ERR_NULL_PTR rather then false for generated funcs ([f0107b4](https://github.com/oonamo/CMyReflection/commit/f0107b40ce335fe864b28c85ad62ed5e0af2c391))
* update readme to be more accurate to test case ([4395758](https://github.com/oonamo/CMyReflection/commit/4395758ba6fd4a74c2aea095c27c6e7a27a647e7))
* update readme to reflect new bounds checking ([7114625](https://github.com/oonamo/CMyReflection/commit/711462508cfface176d89accda72abc7686af5db))
* **windows:** add no secure warnings for windows at top of header ([fbc0994](https://github.com/oonamo/CMyReflection/commit/fbc0994f2b7d06a162560a69f40d01446bd6c628))
* **windows:** add no secure warnings to implementation file ([6bbfe23](https://github.com/oonamo/CMyReflection/commit/6bbfe23544813c8259ceff98fa793417f269a680))


### Miscellaneous Chores

* initial automated release ([e7c8bc6](https://github.com/oonamo/CMyReflection/commit/e7c8bc69cc2a8f01c33156f1de07c8740a27d0de))


### Code Refactoring

* change tags to be namespaced ([6e770cd](https://github.com/oonamo/CMyReflection/commit/6e770cd15066a2aca735ca8770f6483ba00372f4))
* **json:** escape strings and unify write callbacks ([4567b90](https://github.com/oonamo/CMyReflection/commit/4567b9065468bc22f966df8257e036de6b30365a))
* rename *field_tags -&gt; *struct_field_tags ([e105e90](https://github.com/oonamo/CMyReflection/commit/e105e90307b8a395e861b63dd10c8aa4339ee00b))
* rename field extension variables to be clearer ([64fd6b9](https://github.com/oonamo/CMyReflection/commit/64fd6b92b7c9f30bd759687c3ed9557214050268))
* rename FieldInfo -&gt; StructFieldInfo and similar functions for consistency ([76b22a5](https://github.com/oonamo/CMyReflection/commit/76b22a533a631a3ecdb387c0c79ece4c7e2a9d2c))
* rename print plugin to format ([da13d60](https://github.com/oonamo/CMyReflection/commit/da13d6053c83f8454e1f91be112d7e6087feb268))
* rename struct_name field to be more consistent ([175bca6](https://github.com/oonamo/CMyReflection/commit/175bca6cae461d21fb27535f06d5ddb03b3bd118))

# Third-party notices and attribution

The newly authored portions of the `openapi-bindcheck` checker, corpus, reproduction orchestration, and documentation are Copyright (c) 2026 **Zouhair Mudakka**, under the [MIT License](LICENSE). Research, coding, drafting, and review were AI-assisted. This does not confer ownership of upstream code, schemas, tests, or reports.

The project studies existing software and supplies diagnostic corrections using established techniques. Third-party material and derivative corrections retain their applicable upstream terms; the repository's MIT license does not relicense them. References to project names identify the software evaluated and do not imply endorsement.

## Google ADK Python

- Project: [google/adk-python](https://github.com/google/adk-python).
- Source revision: `044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5`.
- License: [Apache License 2.0 at the inspected revision](https://github.com/google/adk-python/blob/044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5/LICENSE).
- The inspected parser source carries **Copyright 2026 Google LLC**. Preserve applicable notices from every fetched file.

ADK provides the actual OpenAPI parser and REST execution implementation. Its unchanged focused tests are used as regression controls. Diagnostic changes to array-body binding and generated-name allocation are modifications prepared for this project's comparison, not upstream releases. Any included excerpts or derivative replacements remain subject to Apache-2.0. The complete license text is reproduced below.

## Prefect FastMCP

- Project: [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp).
- Source revision: `92e44ffcc04b29f960a6c678f44fac226ccc0ea6`.
- License: [Apache License 2.0 at the inspected revision](https://github.com/PrefectHQ/fastmcp/blob/92e44ffcc04b29f960a6c678f44fac226ccc0ea6/LICENSE).

FastMCP supplies the actual OpenAPI-to-MCP implementation and a competent ordinary-collision baseline. Credit is due especially to [#1107](https://github.com/PrefectHQ/fastmcp/pull/1107) for location suffixing and [#5112](https://github.com/PrefectHQ/fastmcp/issues/5112)/[#5113](https://github.com/PrefectHQ/fastmcp/pull/5113) for whole-body collision handling and request-level regression tests. The project does not claim those techniques or tests as its invention.

The diagnostic alias-allocation correction is a local modification of the pinned implementation. Any included excerpts or derivative replacements remain subject to Apache-2.0. Upstream source and test authors retain their rights. The complete license text is reproduced below.

## Open WebUI

- Project: [open-webui/open-webui](https://github.com/open-webui/open-webui).
- Source revision: `8bd8b4fac5e059578ac0c74b3c18d11139f88b7d`.
- License: the custom [Open WebUI License at the inspected revision](https://github.com/open-webui/open-webui/blob/8bd8b4fac5e059578ac0c74b3c18d11139f88b7d/LICENSE), with [LICENSE_HISTORY](https://github.com/open-webui/open-webui/blob/8bd8b4fac5e059578ac0c74b3c18d11139f88b7d/LICENSE_HISTORY) for material governed by prior terms.
- Upstream notice: **Copyright (c) 2023- Open WebUI Inc. [Created by Timothy Jaeryang Baek]**.

Open WebUI is **not** represented as MIT- or Apache-licensed. Its pinned custom license includes notice, endorsement, and branding conditions; the linked upstream text governs. The full Open WebUI application and its upstream implementation file are not vendored in this repository. Reproduction fetches the pinned source and license separately and retains their notices. The component experiment loads the relevant original function bodies locally; it does not import or distribute a complete Open WebUI application.

No Open WebUI correction is supplied. Fetched code remains subject to its applicable upstream terms. Downloading source during reproduction does not relicense it. Credit the original schema-conversion and execution functions and the nearby [#29716](https://github.com/open-webui/open-webui/issues/29716)/[#29717](https://github.com/open-webui/open-webui/pull/29717) report and fix.

## Keycloak

- Project: [keycloak/keycloak](https://github.com/keycloak/keycloak).
- API specimen: [official Admin REST OpenAPI document, version 26.7.4](https://www.keycloak.org/docs-api/26.7.4/rest-api/openapi.json).
- Corresponding source revision: `aa9fe3fba0c6cd5770f19a49378c55f4378cf544` (tag `26.7.4`).
- License: [Apache License 2.0](https://github.com/keycloak/keycloak/blob/aa9fe3fba0c6cd5770f19a49378c55f4378cf544/LICENSE.txt).

The inspected `RealmAdminResource.java` notice credits **Copyright 2016 Red Hat, Inc. and/or its affiliates and other contributors as indicated by the author tags**. Preserve the notices applicable to other fetched files; this example is not a replacement for them.

Keycloak supplies the source API schema and independently documented ordinary-realm rename semantics. The reduced specimen keeps the selected operation and components, adds an operation ID, and points the request at a loopback observer. These are disclosed specimen modifications, not changes to a live Keycloak deployment. No Keycloak server or Java integration test is run by this component experiment. Upstream schema and source material retain Apache-2.0 terms; the complete license text follows.

## Other dependencies and standards

Python packages installed for reproduction retain their individual licenses and notices. They are dependencies of the reproduction environment, not newly authored project code. OpenAPI semantics are attributed to the [OpenAPI Initiative specification](https://spec.openapis.org/oas/v3.0.3.html). The precise prior-work comparisons and search limits are documented in [PRIOR_ART.md](docs/PRIOR_ART.md).

## Apache License 2.0

The following is the complete license text from the inspected Apache-licensed upstream repositories. It applies to their covered material and derivative modifications, not as a replacement for the MIT license on newly authored project material.

```text

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

```

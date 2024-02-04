# BuildInfo Object Model

The [build info](https://buildinfo.org) is an open standard by [JFrog](https://jfrog.io) to store build results. It stores:
- Information about the Build Agent
- Information about the Build Machine
- Information about the produced modules
- Information about the dependencies required to reproduce the results of the build

As the [original work](https://github.com/jfrog/build-info-go) is written in Go and not in python,
this can be considered as a derivative work of the original work, which is published under the Apache License 2.0. So, 
this library comes in two flavors: The Apache License 2.0 due to the usage of the JSON Schema and the MIT License
for the generated and programmed code.

Hence, you can consider the following SPDX-Identifier: Apache 2.0 OR MIT


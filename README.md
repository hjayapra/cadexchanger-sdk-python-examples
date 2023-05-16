# CAD Exchanger SDK examples in Python

This repository contains examples for CAD Exchanger SDK utilizing the Python API.

More information about CAD Exchanger SDK can be found [here](https://cadexchanger.com/products/sdk/). You can find overview of available examples and a brief summary for each one [here](https://docs.cadexchanger.com/sdk/sdk_all_examples.html).

The examples are provided under a permissive Modified BSD License. You may insert their source code into your application and modify as needed.

## Requirements

* Latest version of CAD Exchanger SDK
* Windows x86-64: CPython 3.8 - 3.10
* Linux x86-64: CPython 3.9 - 3.10
* macOS is not supported as of now

## Running

To use the examples, first obtain the CAD Exchanger SDK evaluation [here](https://cadexchanger.com/products/sdk/try/). Upon filling out the form you'll receive an email with an evaluation license key (in `cadex_license.lic` file) and the link to the pip repository containing the CAD Exchanger SDK package.

1. Install the CAD Exchanger SDK package with the following command, substituting `<repo-link-from-email>` for the actual link to pip repository:

    ```
    $ pip install cadexchanger --extra-index-url=<repo-link-from-email>
    ```

    If you get an error message that `pip` was not able to find the package, please check the requirements above and make sure that your configuration is supported.

2. Place the license key into the repository root.

3. Then navigate to your example of choice and launch it with the following command:

    ```
    $ python conversion/transfer/run.py
    ```

    Every `run.py` script first generates a runtime key specific to the sample being launched and then runs the sample with pre-packaged models.

    Learn more about runtime keys and SDK licensing starting from CAD Exchanger 3.18 [here](https://docs.cadexchanger.com/sdk/sdk_licensing.html).

4. Once the `run.py` script has been used at least once and runtime license key is available, you can try out the sample with custom parameters. For example, for `transfer` sample, substitute `<input-model>` for your CAD model that you want to convert and `<output-model>` for the path to the desired result of conversion:

    ```
    $ python conversion/transfer/transfer.py <input-model> <output-model>
    ```

    It's also possible to copy the runtime key creation code from `run.py` to the sample's main source file and use the sample directly right away.

## Learn more

If you'd like to learn more about CAD Exchanger, visit our [website](https://cadexchanger.com/). If you have any questions, please reach out to us [here](https://cadexchanger.com/contact-us/).

# CAD Exchanger SDK examples in Python

This repository contains examples for CAD Exchanger SDK and Manufacturing Toolkit utilizing the Python API.

More information about CAD Exchanger SDK can be found [here](https://cadexchanger.com/products/sdk/). You can find overview of available examples and a brief summary for each one [here](https://docs.cadexchanger.com/sdk/sdk_all_examples.html). More information about Manufacturing Toolkit can be found [here](https://manufacturing.cadexchanger.com/).

The examples are provided under a permissive Modified BSD License. You may insert their source code into your application and modify as needed.

## Requirements

* Latest version of CAD Exchanger SDK
* Windows x86-64: CPython 3.7 - 3.11
* Linux x86-64: CPython 3.7 - 3.11
* macOS Apple Silicon: Python 3.7 - 3.11

## Running

To use the examples, first obtain the CAD Exchanger SDK evaluation [here](https://cadexchanger.com/products/sdk/try/). Upon filling out the form you'll receive an email with an evaluation license key (in `cadex_license.py` file) and the link to the pip repository containing the CAD Exchanger SDK package. You can also register in our [Customer Corner](https://my.cadexchanger.com/) and see both the license key and the repository link there.

1. Install the CAD Exchanger SDK package with the following command, substituting `<repo-link-from-email>` for the actual link to pip repository (found in welcome email or in Customer Corner):

    ```
    $ pip install cadexchanger -i <repo-link-from-email>
    ```

    If you get an error message that `pip` was not able to find the package, please check the requirements above and make sure that your configuration is supported.

2. Place the license key into the repository root.

3. Then launch your example of choice with default arguments by running a command like this:

    ```
    $ python conversion/transfer/run.py
    ```

4. You can also launch each sample with custom parameters. For example, for `transfer` sample, substitute `<input-model>` for your CAD model that you want to convert and `<output-model>` for the path to the desired result of conversion:

    ```
    $ python conversion/transfer/transfer.py <input-model> <output-model>
    ```

    To find out which parameters each sample requires, either launch it without parameters, or view the source code.

## Learn more

If you'd like to learn more about CAD Exchanger, visit our [website](https://cadexchanger.com/). If you have any questions, please reach out to us [here](https://cadexchanger.com/contact-us/).

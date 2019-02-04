# stellar-sandbox
Sandbox for the StellarStation API.

Steps to run the basic example included (commands Debian):

* Install python 3 dependencies and start virtual environment:

```
sudo apt update && sudo apt install python3 python3-virtualenv
virtualenv --python python3 .stellar
source .stellar/bin/activate
pip install -r requirements.txt
```

* Create private keys directory within $HOME:

```
mkdir -p "$HOME/.infostellar"
```

* Download private key from console and store it under "$HOME/.infostellar"
* Return to repository's root and execute the basic example that should list
the services available:

```
python examples/basic.py
```

The class provided within "basic.py" can be used as an initial example of how
to connect a more complex client to StellarStation's API.

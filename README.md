# DVT-relayer

DVT Relayer is a service providing validators' registration data to Stakewise v3-operator
in DVT setup.

As a general introduction in DVT read [the article](https://ethereum.org/en/staking/dvt/) on Ethereum web-site.
For technical details see [Obol docs](https://docs.obol.org/) or [SSV docs](https://docs.ssv.network/).

### Generating DV keystores

Distributed validator (DV) keystores are used:
* on DVT sidecars
* for Relayer testing

The easiest way to generate DV keys for testing is [Obol launchpad](https://holesky.launchpad.obol.org/).
Works for Holesky, Mainnet and Gnosis.
Select "Create a distributed validator alone". Follow instructions. Use vault address as withdrawal address.

In production environment:
* Validators' keystores should be created via distributed key generation (DKG) procedure
* DVT Relayer should not have access to DV keystores.

### Setup

1. Install [poetry](https://python-poetry.org/)
2. `poetry install`
3. `cp .env.example .env`
4. Fill .env file with appropriate values

### Run

1. `poetry shell`
2. `export PYTHONPATH=.`
3. `python src/app.py`

### Test

Running the whole cluster of DVT sidecars locally may be cumbersome.
For testing purpose single sidecar may work on behalf of several DVT operators.
To do that you have to fill `SHARE_INDEXES` in sidecar's environment. For example:
```text
SHARE_INDEXES=1,2,3,4
```

DVT sidecar:
1. Loads DV keystores
2. Polls validator exits from Relayer
3. Pushes exit signature shares to Relayer on behalf of DVT operators.

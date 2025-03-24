# multiobjective-lp

### Installation
See  [TestPyPi](https://test.pypi.org/project/multiobjective-lp/) project page for details

```shell
pip install -i https://test.pypi.org/simple/ multiobjective-lp
```

### Documentation

* Available at https://jasieksz.github.io/multiobjective-lp/
* Documentation is created using MkDocs 
* To deploy new changes run
```shell
cd documentation
make deploy-doc
```


### Code Deployment (Poetry)

#### First time config
1. `poetry config repositories.test-pypi https://test.pypi.org/legacy/`
2. Generate API token
3. `poetry config pypi-token.test-pypi pypi-XXXXX`

#### 
```shell
poetry build
poetry publish -r test-pypi
```

### DEPRECATED  -Code Deployment
1. Configure API key in `~/.pypirc`
2. From repository root directory run the following
    ```shell
    python3 -m build
    python3 -m twine upload --repository testpypi dist/*   
    ```
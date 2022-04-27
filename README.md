# Simple Website generator

This small package generates conference websites with specific standard content (venue, code of conduct, logistics). One defines the content with markdown files, which makes maintenance easy. In addition, the use of GitHub pages allows to deploy the website to a public server quickly.


⚠️ This package is still in development.


## Quick Start

```python
from simplewebsite import generate
generate('docs/config.yml')
```
# SCRiBa

A SCRIpt-BAsed recommender system for movies. SCRiBa computes the similarity 
between movies according to their scripts. Each script is approximated with the
english subtitles available on [OpenSubtitles](
https://www.opensubtitles.org/) and downloadable without restrictions with 
[Tor](https://www.torproject.org/).

Please refer to the [report](report.pdf) and to the [notes](notes.txt) for 
additional details on the algorithm, the pre-processing steps and the 
evaluation on Netflix data.

---
## Information

**Status**: `Completed`

**Type**: `Academic project`

**Course**: `Data Mining`

**Development year(s)**: `2015-2016`

**Authors**: [gcorsi](https://github.com/gcorsi), [ShadowTemplate](
https://github.com/ShadowTemplate)

---
## Getting Started

Each script is required to complete one pre-processing step. Please refer to 
the project report to get information about the pipeline.

### Prerequisites

Clone the repository and install the required Python dependencies:

```
$ git clone https://github.com/ShadowTemplate/scriba.git
$ cd scriba/
$ pip install --user -r requirements.txt
```

[Download the datasets](
https://mega.nz/#!oJlATaZK!2ltn6IStfGFdkHFeIfi5E5DekxXB0POqXtlBetOoiqI).

---
## Building tools

* [Python 3.4](https://www.python.org/downloads/release/python-340/) - 
Programming language
* [Python 2.7](https://www.python.org/downloads/release/python-270/) - 
Programming language
* [scikit-learn](scikit-learn.org/) - TF-IDF features extraction, linear kernel
* [stem](https://pypi.org/project/stem/) - Anonymous and parallel download with 
Tor
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - Web page 
scraping

---
## Contributing

This project is not actively maintained and issues or pull requests may be 
ignored.

---
## License

This project is licensed under the GNU GPLv3 license.
Please refer to the [LICENSE.md](LICENSE.md) file for details.

---
*This README.md complies with [this project template](
https://github.com/ShadowTemplate/project-template). Feel free to adopt it
and reuse it.*

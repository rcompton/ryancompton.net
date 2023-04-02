# -*- coding: utf-8 -*-

import collections
import yaml


# https://stackoverflow.com/questions/9951852/pyyaml-dumping-things-backwards
def order_rep(dumper, data):
    return dumper.represent_mapping(
        "tag:yaml.org,2002:map", data.items(), flow_style=False
    )


yaml.add_representer(collections.OrderedDict, order_rep)


resume = collections.OrderedDict()

contact = collections.OrderedDict()
contact["name"] = "Ryan Compton"
contact["email"] = "ryan@ryancompton.net"
contact["website"] = "http://ryancompton.net/"
resume["contact"] = contact

employment = collections.OrderedDict()
employment[
    "current"
] = "Data Scientist, Clarifai, Designed and constructed datasets in order to improve the performance of deep learning-powered image recognition systems"
employment[
    "2012-2015"
] = "Research Staff, Howard Hughes Research Laboratories, Worked on social media data mining for early detection of newsworthy events."
resume["employment"] = employment

edu = collections.OrderedDict()
edu["PhD"] = [
    "UCLA, Mathematics, 2012",
    "Advised by Chris Anderson",
    'Thesis title "Sparsity Promoting Optimization in Quantum Mechanical Signal Processing"',
]
edu["MS"] = ["UCLA, Mathematics, 2008"]
edu["BA"] = [
    "New College of Florida, Mathematics/Physics, 2006",
    "Advised by Patrick McDonald",
    'Thesis title "Optimizing Cover Times with Constraints"',
]
edu = [
    "PhD, UCLA, Mathematics, 2012",
    "MS, UCLA, Mathematics, 2008",
    "BA, New College of Florida, Mathematics/Physics, 2006",
]
resume["education"] = edu

code = collections.OrderedDict()
code[
    "Python"
] = "Five years, used for machine learning, numerical methods, and visualization."
code["Java"] = "Two years, used for the Hadoop stack, Android, and various web apis."
code["Scala"] = "One year, used for Apache Spark."
code["C++"] = "Three years, used for numerical methods."
code["Matlab"] = "Three years, used for linear algebra and optimization."
resume["code"] = code

pubs = collections.OrderedDict()
pubs["first-authored"] = [
    'Compton, Ryan, Matthew S. Keegan, and Jiejun Xu. "Inferring the geographic focus of online documents from social media sharing patterns." Computational Approaches to Social Modeling (ChASM), 2014.',
    'Compton, Ryan, David Jurgens, and David Allen. "Geotagging One Hundred Million Twitter Accounts with Total Variation Minimization." IEEE BigData, 2014.',
    'Compton, Ryan, et al. "Using publicly visible social media to build detailed forecasts of civil unrest." Springer Security Informatics, 2014.',
    'Compton, Ryan, et al. "Detecting future social unrest in unprocessed Twitter data." Intelligence and Security Informatics (ISI), 2013 IEEE International Conference on. IEEE, 2013. (best paper nomination)',
    'Compton, Ryan, Stanley Osher, and Louis Bouchard. "Hybrid regularization for MRI reconstruction with static field inhomogeneity correction." Biomedical Imaging (ISBI), 2012 9th IEEE International Symposium on. IEEE, 2012.',
    'Compton, Ryan, Hankyu Moon, and Tsai-Ching Lu, "Catastrophe prediction via estimated network autocorrelation." Workshop on Information in Networks, 2011.',
]
pubs["coauthored"] = [
    'Park, Patrick, Ryan Compton and Tsai-Ching Lu. "Network-Based Group Account Classification." Social Computing, Behavioral-Cultural Modeling and Prediction (SBP), 2015. (winner of best paper award)',
    'de Silva, Brian, and Ryan Compton. "Prediction of Foreign Box Office Revenues Based on Wikipedia Page Activity." Computational Approaches to Social Modeling (ChASM), 2014.',
    'Xu, Jiejun, et al. "Quantifying cross-platform engagement through large-scale user alignment." Proceedings of the 2014 ACM conference on Web science. ACM, 2014.',
    'Xu, Jiejun, et al. "Rolling through Tumblr Characterizing behavioral patterns of the microblogging platform." Proceedings of the 2014 ACM conference on Web science. ACM, 2014.',
]
resume["publications"] = pubs


def main():
    resume_str = yaml.dump(resume, indent=4, default_flow_style=False)

    # add blank lines...
    resume_str = resume_str.replace("\neducation", "\n\neducation")
    resume_str = resume_str.replace("\nemployment", "\n\nemployment")
    resume_str = resume_str.replace("\npublications", "\n\npublications")
    resume_str = resume_str.replace("\ncode", "\n\ncode")

    with open("ryan_compton_resume.txt", "w") as fout:
        fout.write(resume_str)

    return


if __name__ == "__main__":
    main()

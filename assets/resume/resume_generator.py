# -*- coding: utf-8 -*-

import collections
import yaml

#https://stackoverflow.com/questions/9951852/pyyaml-dumping-things-backwards
def order_rep(dumper, data):
    return dumper.represent_mapping( u'tag:yaml.org,2002:map', data.items(), flow_style=False )
yaml.add_representer( collections.OrderedDict, order_rep )


resume = collections.OrderedDict()

contact = collections.OrderedDict()
contact['name'] = 'Ryan Compton'
contact['email'] = 'ryan@ryancompton.net'
contact['website'] = 'http://ryancompton.net'
resume['contact'] = contact

resume['employment'] = 'Howard Hughes Research Laboratories, June 2012-present. Work on large-scale social media data mining for early detection of newsworthy events.'

edu = collections.OrderedDict()
edu['PhD'] = ['UCLA, Mathematics, 2012', 'Advised by Chris Anderson', 'Thesis title "Sparsity Promoting Optimization in Quantum Mechanical Signal Processing"']
edu['MS'] = ['UCLA, Mathematics, 2008']
edu['BA'] = ['New College of Florida, Mathematics/Physics, 2006', 'Advised by Patrick McDonald', 'Thesis title "Optimizing Cover Times with Constraints"']
edu = ['PhD, UCLA, Mathematics, 2012',
'MS, UCLA, Mathematics, 2008',
'BA, New College of Florida, Mathematics/Physics, 2006']
resume['education'] = edu


pubs = collections.OrderedDict()
pubs['first-authored'] = ['Compton, Ryan, Matthew S. Keegan, and Jiejun Xu. "Inferring the geographic focus of online documents from social media sharing patterns." Computational Approaches to Social Modeling (ChASM), 2014.',
'Compton, Ryan, David Jurgens, and David Allen. "Geotagging One Hundred Million Twitter Accounts with Total Variation Minimization." IEEE BigData, 2014.',
'Compton, Ryan, et al. "Using publicly visible social media to build detailed forecasts of civil unrest." Springer Security Informatics, 2014.',
'Compton, Ryan, et al. "Detecting future social unrest in unprocessed Twitter data." Intelligence and Security Informatics (ISI), 2013 IEEE International Conference on. IEEE, 2013. (best paper nomination)',
'Compton, Ryan, Stanley Osher, and Louis Bouchard. "Hybrid regularization for MRI reconstruction with static field inhomogeneity correction." Biomedical Imaging (ISBI), 2012 9th IEEE International Symposium on. IEEE, 2012.',
'Ryan Compton, Hankyu Moon, and Tsai-Ching Lu, "Catastrophe prediction via estimated network autocorrelation." Workshop on Information in Networks, 2011.'
]
pubs['coauthored'] = ['de Silva, Brian, and Ryan Compton. "Prediction of Foreign Box Office Revenues Based on Wikipedia Page Activity." Computational Approaches to Social Modeling (ChASM), 2014.',
'Xu, Jiejun, et al. "Quantifying cross-platform engagement through large-scale user alignment." Proceedings of the 2014 ACM conference on Web science. ACM, 2014.',
'Xu, Jiejun, et al. "Rolling through Tumblr Characterizing behavioral patterns of the microblogging platform." Proceedings of the 2014 ACM conference on Web science. ACM, 2014.'
]
resume['publications'] = pubs 


code = collections.OrderedDict()
code['Python'] = 'Five years, used for machine learning, numerical methods, and visualization, e.g. http://bitbucket.org/rcompton/fft-sonification'
code['Java'] = 'Two years, used for the Hadoop stack, Android, and various web apis, e.g. http://code.google.com/p/ndbc-buoy4j'
code['Scala'] = 'One year, used for Apache Spark, e.g. http://arxiv.org/abs/1404.7152'
code['C++'] = 'Three years, used for numerical methods, e.g. http://bitbucket.org/rcompton/fftw-boost-wrapper'
code['Matlab'] = 'Three years, used for linear algebra and optimization, e.g. http://code.google.com/p/framelet-mri'
resume['code'] = code


def main():

    resume_str = yaml.dump(resume, indent=4, default_flow_style=False)

    #add blank lines...
    resume_str = resume_str.replace('\neducation', '\n\neducation')
    resume_str = resume_str.replace('\nemployment', '\n\nemployment')
    resume_str = resume_str.replace('\npublications', '\n\npublications')
    resume_str = resume_str.replace('\ncode', '\n\ncode')



    with open('ryan_compton_resume.yaml','w') as fout:
        fout.write(resume_str)


    return

if __name__ == '__main__':
    main()
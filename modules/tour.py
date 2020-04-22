from . import config
from . import stixhelpers
from . import  util
import os

def generate_tour():
    """Responsible for dynamically generating tour steps
    """

    # Algorithm
    # For each domain:
    # 1. index (start page, doesn't need to be dynamic)
    # 2. A matrix with sub-techniques
    # 3. A technique with sub-techniques
    # 4. One of the sub-techniques of that technique
    # 5. A group/software that meets the following criteria:
    # 5.1. Group has a relationship with a technique but not that technique's sub-techniques
    # 5.2. Group has a relationship with a technique and (preferably) 2+ of that technique's sub-techniques
    # 5.3. Group has a relationship with (preferably) 2+ sub-techniques but not the parent technique.
    #      If any of the above criteria are not met by any software/group, that section of the group/software page of the tour can be skipped.

    tours = []
    for matrix in config.matrices:
        if matrix["type"] == "external": continue # link to externally hosted matrix, ignore it
        tours.append(get_tour_steps(matrix))
    
    # Choose longest tour
    def get_longest_tour():

        if tours:
            longest = {}
            for tour in tours:
                if len(tour.keys()) > len(longest.keys()):
                    longest = tour
            
            return longest
        
        return {}

    tour_steps = get_longest_tour()

    # Write tour steps to settings.js file
    javascript_settings_file = os.path.join(config.javascript_path, "settings.js")

    with open(javascript_settings_file, "a+", encoding='utf8') as js_f:
        js_data = config.js_tour_settings.substitute({"tour_steps": tour_steps})
        js_f.write(js_data)
    
def get_tour_steps(matrix):

    ms = config.ms[matrix['matrix']]

    # Reads the STIX and creates a list of the techniques
    techniques = stixhelpers.get_techniques(ms)

    techs_no_subtechs = util.filter_out_subtechniques(techniques)
    techs_with_subtechs = util.filter_out_techniques_without_subtechniques(techniques)

    # steps as array
    steps = {}

    # If matrix has techniques with subtechniques
    if techs_with_subtechs:
        steps['matrix'] = "matrices/" + matrix['path']
    else:
        return steps
    
    # Find technique with sub-techniques
    technique = get_technique_with_subtechniques(techs_no_subtechs)

    # Get technique ID and store that as the step
    steps['technique'] = "techniques/{}".format(util.get_attack_id(technique))
    steps['subtechnique'] = steps['technique'] + "/{}".format(get_subtech_n_of_technique(technique))
    return steps

def get_technique_with_subtechniques(techs_no_subtechs):
    """ Find first technique with at least 4 sub-techniques and return technique
        Return technique with the most sub-techniques if not the case 
    """

    counter = 0
    chosen_tech = {}
    for tech in techs_no_subtechs:
        if tech["id"] in config.subtechniques_of:

            # Grab sub-technique count from technique
            subtech_count =  len(config.subtechniques_of[tech["id"]])
            # Check if sub-technique count is bigger than counter
            if counter < subtech_count:
                # Quick return if found
                if subtech_count > 3: return tech
                # Set counter and new techique
                counter = subtech_count
                chosen_tech = tech
    
    return chosen_tech

def get_subtech_n_of_technique(technique):
    """ Return ID number of first sub-technique of given technique """

    for subtech in config.subtechniques_of[technique['id']]:
        id = util.get_attack_id(subtech['object'])
        return id.split(".")[1]
         
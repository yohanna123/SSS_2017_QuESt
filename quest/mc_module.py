"""
This module will take in the sigma and epsilon parameters and will do a Monte Carlo simulation
"""

import numpy as np
import sys
from core import core
#from . import core


def tail_correction(box_length, cutoff, num_particles):
    """
    This is correction function to the potential energy. The correction function
    is used to compensate the switch off the LJ potential after rcutoff

    The function is U*corr = (8*pi*num_particles^2)/(3*volume)*[(1/3)*(1/cutoff)^9-(1/cutoff)^3]

    defined the box length for a cubic box, cutoff = 3*sigma,
    where sigma is the distance where the LJ potential is zero
    """

    if not (isinstance(box_length, float) and isinstance(cutoff, float)):
        raise ValueError('Box length and cutoff must be float')

    if (box_length < 0.0) or (cutoff < 0.0):
        raise ValueError('Box length and cutoff must be positive')

    volume = box_length**3
    sig_by_cutoff3 = (1 / cutoff)**3
    sig_by_cutoff9 = sig_by_cutoff3**3
    e_correction = sig_by_cutoff9 - 3.0 * sig_by_cutoff3
    e_correction *= 8.0 / 9.0 * np.pi * num_particles**2 / volume
    return e_correction


def rdf_func(coordinates_NIST, bins, box_length, reduced_density, number_of_snapshots):
    """

    This function calculates the radial distribution function for a system of LJ particles in a cubic box

                                                  -----Parameters-----
    coordinates_NIST: 
        coordinates generated by Monte Carlo user can defined number of concentric sphere to be considered for
    bins:
        User defined number of concentric sphere for rdf calculation
    reduced_density:
        Density of the system in reduced unit
    box_length :
        Same as used in Monte_carlo
    num_of_snapshots :
        Number of times coordinates taken from Monte_carlo
    """
    if number_of_snapshots == 1:
        gr = np.zeros((bins), dtype=float)
        gr_ideal = np.zeros((bins), dtype=float)
        delta_r = (box_length / 2.0) / bins
        rcutoff2 = np.power(box_length/2., 2) ## uses in rdf calculation
        r_domain = np.linspace(0.0, box_length/2., bins)
        const = 4.0 * reduced_density * np.pi / 3.0

        for i_bin in range(0, bins):
            r_lower = i_bin * delta_r
            r_upper = r_lower + delta_r
            n_ideal = const * (np.power(r_upper, 3) - np.power(r_lower, 3))
            gr_ideal[i_bin] = n_ideal

    num_particles = len(coordinates_NIST)
    gr = core.rdf(delta_r, gr, coordinates_NIST[:, 0], coordinates_NIST[:, 1], coordinates_NIST[:, 2], box_length,
                rcutoff2)
    current_gr = gr / gr_ideal / number_of_snapshots / num_particles
    gr_max = np.amax(current_gr)
    r_domain_index = np.argmax(current_gr)
    r_domain_max = r_domain[r_domain_index]
    return (r_domain, current_gr, gr_max, r_domain_max)


#def lennard_jones_potential(rij2): ## commented by dibyendu ##
#    sig_by_r6 = (1 / rij2)**3
#    sig_by_r12 = sig_by_r6**2
#    return 4.0 * (sig_by_r12 - sig_by_r6)


#def minimum_image_distance(r_i, r_j, box_length): ## commented by dibyendu ##
#    rij = r_i - r_j
#    rij -= box_length * np.round(rij / box_length)
#    rij2 = np.dot(rij, rij)
#    return rij2


#def tail_correction(box_length):   ## commented by dibyendu ##
#    volume = box_length**3
#    sig_by_cutoff3 = (1 / cutoff)**3
#    sig_by_cutoff9 = sig_by_cutoff3**3
#    e_correction = sig_by_cutoff9 - 3.0 * sig_by_cutoff3
#    e_correction *= 8.0 / 9.0 * np.pi * num_particles**2 / volume
#    return e_correction

def monte_carlo(epsilon,
                box_length,
                cutoff,
                num_steps):
    """
    Runs MC simulation using the MCMC algorithm.
    Conformations are chosen from a probability density based on the Metropolis Hastings criteria
    for acceptance

    ------------
    PARAMETERS
    epsilon:
        passed in from lj fitting in order to convert reduced units to real units.
    box_length:
        decides the size of the box
    cutoff:
        determines the distance in which pair-wise energies are to be calculated.
    num_steps:
        controls how many iterations the MC simulation will occur. start sampling
        after 30,000 steps to ensure equilibration.
    reduced_temp:
        temperature of the system in reduced unit (NVT ensemble) 
    tolerance_acce_rate:
        controls the limits of accepting/rejecting conformational states.
    max_displacement_scaling:
        controls how much the atoms should be displaced, so that we
        obtain more conformations within our tolerance acceptance rate.

    returns:
        total energy and array of accepted coordinates.

#    """
    reduced_density = 0.9
    reduced_temperature = 0.9
    temperature = reduced_temperature * epsilon
    beta = 1. / temperature
    coordinates_NIST = np.loadtxt("lj_sample_config_periodic1.txt", skiprows=2, usecols=(1, 2, 3))
    num_particles = len(coordinates_NIST)
    coordinates_of_simulation = np.zeros((num_steps*num_particles, 3)) #where simulation coordinates will be stored.
    num_accept = 0
    num_trials = 0
    max_displacement = 0.1
    count = 0  # for storing accepted conformations
    cutoff2 = np.power(cutoff,2)
    energy_array = np.zeros(num_steps)
    num_accept = 0
    num_trials = 0
    total_pair_energy = core.system_energy(coordinates_NIST[:,0], coordinates_NIST[:,1], coordinates_NIST[:,2], box_length, cutoff2, epsilon)
    tail_corr = tail_correction(box_length, cutoff, num_particles) ## total_pair_energy and tail_correction added by dibyendu

    for i_step in range(num_steps):
        num_trials += 1
        i_particle = np.random.randint(num_particles)
        old_position = coordinates_NIST[i_particle].copy()
        old_energy = core.pair_energy(i_particle, coordinates_NIST[:, 0], coordinates_NIST[:, 1], coordinates_NIST[:, 2],
                                    box_length, cutoff2, epsilon)
        random_displacement = (np.random.rand(3) - 0.5) * 2 * max_displacement
        coordinates_NIST[i_particle] += random_displacement
        new_energy = core.pair_energy(i_particle, coordinates_NIST[:, 0], coordinates_NIST[:, 1], coordinates_NIST[:, 2],
                                    box_length, cutoff2, epsilon)
        delta_energy = new_energy - old_energy
        if delta_energy < 0.0:
            accept = True
            coordinates_of_simulation[count] = coordinates_NIST[i_particle]
            count += 1
        else:
            random_number = np.random.rand(1)
            p_acc = np.exp(-beta * delta_energy)
            if random_number < p_acc:
                accept = True
                coordinates_of_simulation[count] = coordinates_NIST[i_particle]
                count += 1
            else:
                accept = False

        if accept:
            num_accept += 1
            total_pair_energy += delta_energy
            
        else:
            coordinates_NIST[i_particle] -= random_displacement

        if np.mod(i_step + 1, 1000) == 0:
            acc_rate = float(num_accept) / float(num_steps)
            num_accept = 0
            num_trials = 0
            if acc_rate < 0.38:
                max_displacement *= 0.8
            elif acc_rate > 0.42:
                max_displacement *= 1.2
        total_energy = (total_pair_energy + tail_corr) / num_particles
        energy_array[i_step] = total_energy
        #print("total energy:")
        #print(total_energy * num_particles)
    #print(energy_array)
    return (energy_array, coordinates_of_simulation) ## coordinates_of_simulation added by dibyendu

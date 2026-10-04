from util import *
import numpy as np
import random
import time
import gurobipy as gp
from gurobipy import GRB

def try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle2):
    merged_orders = bundle1.shop_seq + bundle2.shop_seq
    total_volume = get_total_volume(all_orders, merged_orders)

    if bundle1.rider.type == bundle2.rider.type:
        riders = [bundle1.rider]
    else:
        riders = [bundle1.rider, bundle2.rider]

    shortest_distance = float('inf')
    best_shop_perm = None
    best_dlv_perm = None

    for rider in riders:
        # We skip the test if there are too many orders
        if total_volume <= rider.capa and len(merged_orders) <= 5:
            for shop_perm in permutations(merged_orders):
                for dlv_perm in permutations(merged_orders):
                    feasibility_check = test_route_feasibility(all_orders, rider, shop_perm, dlv_perm)
                    if feasibility_check == 0:  # feasible!
                        total_dist = get_total_distance(K, dist_mat, shop_perm, dlv_perm)
                        if total_dist < shortest_distance:
                            shortest_distance = total_dist
                            best_shop_perm = shop_perm
                            best_dlv_perm = dlv_perm

    if best_shop_perm is not None and best_dlv_perm is not None:
        return Bundle(all_orders, rider, list(best_shop_perm), list(best_dlv_perm),
                      bundle1.total_volume + bundle2.total_volume, shortest_distance)

    return None

def find_feasible_index(valid_indices):
    if len(valid_indices) == 0:
        raise ValueError("All values in dist_matrix3 are infeasible (np.inf or NaN).")

    choice_index = np.random.choice(len(valid_indices))
    choice = tuple(valid_indices[choice_index])

    return choice, choice_index

def find_bundle_by_index(single_index_mapping, index):
    return single_index_mapping.get(index, None)

def find_bundle_by_indices(pair_index_mapping, index1, index2):
    return pair_index_mapping.get((index1, index2), None)

def find_bundle_by_three_indices(triple_index_mapping, index1, index2, index3):
    return triple_index_mapping.get((index1, index2, index3), None)
def bundling_123(K, all_orders, all_riders, ready_time_vec, deadline_vec, volume_vec, dist_mat):
    start_time = time.time()
    best_sequences = {0: {}, 1: {}, 2: {}}
    bike_riders = []
    car_riders = []
    walk_riders = []

    for rider in all_riders:
        if rider.type == 'BIKE':
            bike_riders.append(rider)
            bike_rider = rider
        elif rider.type == 'CAR':
            car_riders.append(rider)
            car_rider = rider
        else:  # Assuming the only other type is WALK
            walk_riders.append(rider)
            walk_rider = rider

    # Combine the lists, with BIKE riders at the end
    ordered_riders = walk_riders + car_riders  + bike_riders
    feasible_pairs_by_rider = {}
    for rider in ordered_riders:
        capa = rider.capa
        pickup_dist = rider.T[:K, :K]
        delivery_dist = rider.T[K:, K:]
        pdp_dist = rider.T[:K, K:]

        # bundle1
        bundle1_dist = np.diag(pdp_dist)
        capacity_feasibility_single = capa >= volume_vec
        feasible_matrix1 = (ready_time_vec + bundle1_dist <= deadline_vec) & capacity_feasibility_single

        bundle1 = []
        for i in range(K):
            if feasible_matrix1[i]:
                shop_seq = [int(i)]
                dlv_seq = [int(i)]
                total_volume = volume_vec[i]
                new_bundle = Bundle(
                    all_orders,
                    rider,
                    shop_seq,
                    dlv_seq,
                    total_volume,
                    dist_mat[i, i + K]
                )
                bundle1.append(new_bundle)

        best_sequences[0][rider.type] = bundle1

        # Bundle 2
        # Capacity feasibility for bundles
        capacity_feasibility = capa >= (volume_vec[:, np.newaxis] + volume_vec[np.newaxis, :])

        ## Because matrices pickup 0->1 and delivery 0->1, the pdp should be 1 -> 0
        pdp = pdp_dist.T

        ## And same logic for pdp, pickup and delivery matrices 0->1 ,therefore pdp.same should be 1->0
        pdp_same = np.broadcast_to(np.diag(pdp_dist)[:, np.newaxis], pdp_dist.shape).T

        different_distance = pickup_dist + pdp + delivery_dist
        same_distance = pickup_dist + pdp_same + delivery_dist

        ## Create Ready time and deadline matrices
        ready_time_matrix = np.tile(ready_time_vec, (K, 1))
        deadline_matrix = np.tile(deadline_vec, (K, 1))

        start_time_1 = ready_time_matrix.T + pickup_dist

        start_time_2 = np.maximum(start_time_1 + pdp, ready_time_matrix + pdp)
        start_time_2_2 = np.maximum(start_time_1 + pdp_same, ready_time_matrix + pdp_same)
        end_time_1 = start_time_2 + delivery_dist
        end_time_1_2 = start_time_2_2 + delivery_dist

        time_feasibility = (start_time_2 <= deadline_matrix.T) & (end_time_1 <= deadline_matrix)
        time_feasibility2 = (start_time_2_2 <= deadline_matrix) & (end_time_1_2 <= deadline_matrix.T)
        combined_feasibility = capacity_feasibility & time_feasibility
        combined_feasibility2 = capacity_feasibility & time_feasibility2

        bundle2_dist_1 = np.where(combined_feasibility, different_distance, np.inf)
        bundle2_dist_2 = np.where(combined_feasibility2, same_distance, np.inf)

        # Ensure diagonal elements are np.inf
        np.fill_diagonal(bundle2_dist_1, np.inf)
        np.fill_diagonal(bundle2_dist_2, np.inf)

        # Stack the distances for comparison
        stacked_distances = np.stack((bundle2_dist_1, bundle2_dist_2, bundle2_dist_1.T, bundle2_dist_2.T), axis=2)

        # Find the indices of the upper triangle excluding the diagonal
        upper_triangle_indices = np.triu_indices(K, 1)

        # Get the minimum distances and their indices for the upper triangle
        min_indices_upper = np.argmin(stacked_distances[upper_triangle_indices], axis=1)

        # List to hold the bundles
        bundle2 = []

        feasible_pairs = set()

        for idx, (i, j) in enumerate(zip(*upper_triangle_indices)):
            if np.all(stacked_distances[i, j] == np.inf):
                continue
            else:
                i = int(i)
                j = int(j)
                min_index = min_indices_upper[idx]
                if min_index == 0:
                    shop_seq = [i, j]
                    dlv_seq = [i, j]
                elif min_index == 1:
                    shop_seq = [i, j]
                    dlv_seq = [j, i]
                elif min_index == 2:
                    shop_seq = [j, i]
                    dlv_seq = [j, i]
                else:
                    shop_seq = [j, i]
                    dlv_seq = [i, j]

                total_volume = volume_vec[shop_seq[0]] + volume_vec[shop_seq[1]]
                new_bundle = Bundle(
                    all_orders,
                    rider,
                    shop_seq,
                    dlv_seq,
                    total_volume,
                    get_total_distance(K, dist_mat, shop_seq, dlv_seq)
                )
                bundle2.append(new_bundle)
                feasible_pairs.add(frozenset(shop_seq))

        best_sequences[1][rider.type] = bundle2
        feasible_pairs_by_rider[rider.type] = feasible_pairs

        print('Time taken for bundling 2:', time.time() - start_time)
    ## Bundle 3 Precaluate the distances
    ## We just need to find the minimum distance, right now, this is time (by bike) but if only we can find miminum it doesn't matter)
    ## I recalculate the distance using utils.get_total_distance because I see that the calculation is slightly different than what I calculate
    ## I think it is because of rounding number
    ## Currently, this calculation is by bike
    i, j, k = np.indices((K, K, K))

    pickup_tensor = pickup_dist[i, j] + pickup_dist[j, k]
    delivery_tensor = delivery_dist[i, j] + delivery_dist[j, k]
    print('Time taken for bundling 3_0:', time.time() - start_time)

    pickup_tensor1 = pickup_tensor + pdp
    pickup_tensor2 = pickup_tensor + pdp[k,k]
    pickup_tensor3 = pickup_tensor + pdp[k,i].T
    print('Time taken for bundling 3_0_1:', time.time() - start_time)
    distance1 = pickup_tensor1 + delivery_tensor[j,k,i]
    distance1_2 = pickup_tensor1+ delivery_tensor[j,i,k]
    distance2 = pickup_tensor2  + delivery_tensor[k,j,i]
    distance2_2 = pickup_tensor2  + delivery_tensor[k,i,j]
    distance3 = pickup_tensor3  + delivery_tensor[i,j,k]
    distance3_2 = pickup_tensor3 + delivery_tensor[i,k,j]
    print('Time taken for bundling 3_0_2:', time.time() - start_time)

    ## Process riders in the order of bike, car and walk
    reordered_riders =  bike_riders + car_riders + walk_riders
    feasible_triplets_by_rider = {}
    for rider in reordered_riders:
        ## Reuse pickup tensor and delivery tensor by just recalculating
        if rider.type == 'CAR':
            capa = rider.capa
            pickup_dist = rider.T[:K, :K]
            delivery_dist = rider.T[K:, K:]
            pdp_dist = rider.T[:K, K:]
            pdp = pdp_dist.T
            pickup_tensor = ((pickup_tensor - bike_rider.service_time*2)*bike_rider.speed/car_rider.speed) + car_rider.service_time*2
            delivery_tensor = ((delivery_tensor - bike_rider.service_time*2)*bike_rider.speed/car_rider.speed) + car_rider.service_time*2
        if rider.type == 'WALK':
            capa = rider.capa
            pickup_dist = rider.T[:K, :K]
            delivery_dist = rider.T[K:, K:]
            pdp_dist = rider.T[:K, K:]
            pdp = pdp_dist.T
            pickup_tensor = ((pickup_tensor - car_rider.service_time*2)*car_rider.speed/walk_rider.speed) + walk_rider.service_time*2
            delivery_tensor = ((delivery_tensor - car_rider.service_time*2)*car_rider.speed/walk_rider.speed) + walk_rider.service_time*2


        ## compare with ready Time1
        start_time_tensor = np.maximum(ready_time_matrix.T+ pickup_dist, ready_time_matrix)

        start_time_tensor_check = start_time_tensor[i,j]+pickup_dist[j,k]
        k_ready_time_tensor = ready_time_vec[np.newaxis, np.newaxis, :]

        # Compare with k-th ready time
        start_time_tensor_final = np.maximum(start_time_tensor_check, k_ready_time_tensor)

        print('Time taken for bundling 3_0_2_1:', time.time() - start_time)

        ## Calculate the end time1
        end_time_tensor1 = start_time_tensor_final[i,j,k] + pdp ##k,j
        end_time_tensor1_2 = start_time_tensor_final + pdp[k,k]
        end_time_tensor1_3 = start_time_tensor_final + pdp[k,i].T

        print('Time taken for bundling 3_0_3:', time.time() - start_time)

        ## Calculate the end time2, The pickup has 3 index, it represent any shop sequence
        ## However, the delivery need to be calculated based on the shop sequence
        ## In total there are 36 combinations but we only need to calculate 6 combinations of shop sequence
        end_time_tensor2_aa = end_time_tensor1 + delivery_dist[j,k]
        end_time_tensor2_ab = end_time_tensor1 + delivery_dist[j,i]
        end_time_tensor2_bb = end_time_tensor1_2 + delivery_dist[k,j]
        end_time_tensor2_bc = end_time_tensor1_2 + delivery_dist[k,i]
        end_time_tensor2_cc = end_time_tensor1_3 + delivery_dist[i,j]
        end_time_tensor2_cd = end_time_tensor1_3 + delivery_dist[i,k]
        print('Time taken for bundling 3_0_4:', time.time() - start_time)

        ## Calculate the end time3
        end_time_tensor3_aa = end_time_tensor2_aa + delivery_dist[k,i]
        end_time_tensor3_ab = end_time_tensor2_ab + delivery_dist[i,k]
        end_time_tensor3_bb = end_time_tensor2_bb + delivery_dist[j,i]
        end_time_tensor3_bc = end_time_tensor2_bc + delivery_dist[i,j]
        end_time_tensor3_cc = end_time_tensor2_cc + delivery_dist[j,k]
        end_time_tensor3_cd = end_time_tensor2_cd + delivery_dist[k,j]

        print('Time taken for bundling 3_1:', time.time() - start_time)
        deadline_tensor = deadline_vec[:, np.newaxis, np.newaxis]
        deadline_tensor2 = deadline_vec[np.newaxis, :, np.newaxis]
        deadline_tensor3 = deadline_vec[np.newaxis, np.newaxis, :]

        # Compare end times with appropriate deadlines
        time_feasibility_tensor_aa = (end_time_tensor1 <= deadline_tensor[j, :, :].squeeze()) & \
                                     (end_time_tensor2_aa <= deadline_tensor2[:, k, :].squeeze()) & \
                                     (end_time_tensor3_aa <= deadline_tensor3[:, :, i].squeeze())

        time_feasibility_tensor_ab = (end_time_tensor1 <= deadline_tensor[j, :, :].squeeze()) & \
                                     (end_time_tensor2_ab <= deadline_tensor2[:, i, :].squeeze()) & \
                                     (end_time_tensor3_ab <= deadline_tensor3[:, :, k].squeeze())

        time_feasibility_tensor_bb = (end_time_tensor1_2 <= deadline_tensor[k, :, :].squeeze()) & \
                                     (end_time_tensor2_bb <= deadline_tensor2[:, j, :].squeeze()) & \
                                     (end_time_tensor3_bb <= deadline_tensor3[:, :, i].squeeze())

        time_feasibility_tensor_bc = (end_time_tensor1_2 <= deadline_tensor[k, :, :].squeeze()) & \
                                     (end_time_tensor2_bc <= deadline_tensor2[:, i, :].squeeze()) & \
                                     (end_time_tensor3_bc <= deadline_tensor3[:, :, j].squeeze())

        time_feasibility_tensor_cc = (end_time_tensor1_3 <= deadline_tensor[i, :, :].squeeze()) & \
                                     (end_time_tensor2_cc <= deadline_tensor2[:, j, :].squeeze()) & \
                                     (end_time_tensor3_cc <= deadline_tensor3[:, :, k].squeeze())

        time_feasibility_tensor_cd = (end_time_tensor1_3 <= deadline_tensor[i, :, :].squeeze()) & \
                                     (end_time_tensor2_cd <= deadline_tensor2[:, k, :].squeeze()) & \
                                     (end_time_tensor3_cd <= deadline_tensor3[:, :, j].squeeze())

        print('Time taken for bundling 3_2:', time.time() - start_time)

        volume_tensor = volume_vec[:, np.newaxis, np.newaxis] + volume_vec[np.newaxis, :, np.newaxis] + volume_vec[
                                                                                                        np.newaxis,
                                                                                                        np.newaxis, :]
        # Check if the total volume is within the capacity
        capacity_feasibility_tensor = volume_tensor <= capa

        combined_feasibility_tensor_aa = capacity_feasibility_tensor & time_feasibility_tensor_aa
        combined_feasibility_tensor_ab = capacity_feasibility_tensor & time_feasibility_tensor_ab
        combined_feasibility_tensor_bb = capacity_feasibility_tensor & time_feasibility_tensor_bb
        combined_feasibility_tensor_bc = capacity_feasibility_tensor & time_feasibility_tensor_bc
        combined_feasibility_tensor_cc = capacity_feasibility_tensor & time_feasibility_tensor_cc
        combined_feasibility_tensor_cd = capacity_feasibility_tensor & time_feasibility_tensor_cd

        bundle3_dist_aa = np.where(combined_feasibility_tensor_aa, distance1, np.inf)
        bundle3_dist_ab = np.where(combined_feasibility_tensor_ab, distance1_2, np.inf)
        bundle3_dist_bb = np.where(combined_feasibility_tensor_bb, distance2, np.inf)
        bundle3_dist_bc = np.where(combined_feasibility_tensor_bc, distance2_2, np.inf)
        bundle3_dist_cc = np.where(combined_feasibility_tensor_cc, distance3, np.inf)
        bundle3_dist_cd = np.where(combined_feasibility_tensor_cd, distance3_2, np.inf)

        ## Stack the distances for comparison
        stacked_distances = np.stack((bundle3_dist_aa, bundle3_dist_ab, bundle3_dist_bb, bundle3_dist_bc, bundle3_dist_cc, bundle3_dist_cd), axis=2)
        print('Time taken for bundling 3_3_2:', time.time() - start_time)
        # Find the indices of the upper triangle excluding the diagonal for a 4D tensor
        # Ensure valid dimensions for i, j, k
        i, j, k = np.array(i), np.array(j), np.array(k)
        mask = (i < j) & (j < k)

        # Apply the mask to get valid indices
        valid_indices = np.vstack((i[mask], j[mask], k[mask])).T
        bundle3 = []
        rider_feasible_pairs = feasible_pairs_by_rider[rider.type]

        print('Time taken for bundling 3_3:', time.time() - start_time)

        # Precompute the inf check mask to avoid repeated np.all calls
        inf_mask = (
                np.all(stacked_distances[valid_indices[:, 0], valid_indices[:, 1], :, valid_indices[:, 2]] == np.inf,
                       axis=-1) &
                np.all(stacked_distances[valid_indices[:, 0], valid_indices[:, 2], :, valid_indices[:, 1]] == np.inf,
                       axis=-1) &
                np.all(stacked_distances[valid_indices[:, 1], valid_indices[:, 0], :, valid_indices[:, 2]] == np.inf,
                       axis=-1) &
                np.all(stacked_distances[valid_indices[:, 1], valid_indices[:, 2], :, valid_indices[:, 0]] == np.inf,
                       axis=-1) &
                np.all(stacked_distances[valid_indices[:, 2], valid_indices[:, 0], :, valid_indices[:, 1]] == np.inf,
                       axis=-1) &
                np.all(stacked_distances[valid_indices[:, 2], valid_indices[:, 1], :, valid_indices[:, 0]] == np.inf,
                       axis=-1)
        )

        # Filter out indices with all np.inf distances
        valid_indices = valid_indices[~inf_mask]
        feasible_triplets = set()

        for idx_i, idx_j, idx_k in valid_indices:
            ## avoid invalid pairs from previous bundling 2
            if (frozenset([idx_i, idx_j]) not in rider_feasible_pairs or
                    frozenset([idx_j, idx_k]) not in rider_feasible_pairs or
                    frozenset([idx_i, idx_k]) not in rider_feasible_pairs):
                continue

            ## Find the minimum distance
            distances = [
                (
                np.min(stacked_distances[idx_i, idx_j, :, idx_k]), np.argmin(stacked_distances[idx_i, idx_j, :, idx_k]),
                [idx_i, idx_j, idx_k]),
                (
                np.min(stacked_distances[idx_i, idx_k, :, idx_j]), np.argmin(stacked_distances[idx_i, idx_k, :, idx_j]),
                [idx_i, idx_k, idx_j]),
                (
                np.min(stacked_distances[idx_j, idx_i, :, idx_k]), np.argmin(stacked_distances[idx_j, idx_i, :, idx_k]),
                [idx_j, idx_i, idx_k]),
                (
                np.min(stacked_distances[idx_j, idx_k, :, idx_i]), np.argmin(stacked_distances[idx_j, idx_k, :, idx_i]),
                [idx_j, idx_k, idx_i]),
                (
                np.min(stacked_distances[idx_k, idx_i, :, idx_j]), np.argmin(stacked_distances[idx_k, idx_i, :, idx_j]),
                [idx_k, idx_i, idx_j]),
                (
                np.min(stacked_distances[idx_k, idx_j, :, idx_i]), np.argmin(stacked_distances[idx_k, idx_j, :, idx_i]),
                [idx_k, idx_j, idx_i])
            ]

            min_distance, selected_min_index, shop_seq = min(distances, key=lambda x: x[0])

            dlv_seq_lookup = {
                0: [shop_seq[1], shop_seq[2], shop_seq[0]],
                1: [shop_seq[1], shop_seq[0], shop_seq[2]],
                2: [shop_seq[2], shop_seq[1], shop_seq[0]],
                3: [shop_seq[2], shop_seq[0], shop_seq[1]],
                4: [shop_seq[0], shop_seq[1], shop_seq[2]],
                5: [shop_seq[0], shop_seq[2], shop_seq[1]]
            }

            dlv_seq = dlv_seq_lookup[selected_min_index]

            total_volume = volume_vec[shop_seq[0]] + volume_vec[shop_seq[1]] + volume_vec[shop_seq[2]]

            ## The shop_seq and dlv_seq should be in integer (Solution requriement)
            shop_seq = list(map(int, shop_seq))
            dlv_seq = list(map(int, dlv_seq))
            new_bundle = Bundle(
                all_orders,
                rider,
                shop_seq,
                dlv_seq,
                total_volume,
                get_total_distance(K, dist_mat, shop_seq, dlv_seq)
            )
            feasible_triplets.add(frozenset(shop_seq))
            bundle3.append(new_bundle)

        best_sequences[2][rider.type] = bundle3
        feasible_triplets_by_rider[rider.type] = feasible_triplets

        print('Time taken for bundling 3_4:', time.time() - start_time)

    return best_sequences, feasible_triplets_by_rider



def algorithm(K, all_orders, all_riders, dist_mat, timelimit=60):
    start_time = time.time()

    for r in all_riders:
        r.T = np.round(dist_mat / r.speed + r.service_time)

    solution = []

    seed = 0
    np.random.seed(seed)
    random.seed(seed)

    ready_time_vec = np.array([order.ready_time for order in all_orders])
    deadline_vec = np.array([order.deadline for order in all_orders])
    volume_vec = np.array([order.volume for order in all_orders])

    riders_dict = {r.type: r for r in all_riders}
    walk_rider = riders_dict['WALK']
    bike_rider = riders_dict['BIKE']
    car_rider = riders_dict['CAR']

    best_sequences, feasible_triplets_by_rider = bundling_123(K, all_orders, all_riders, ready_time_vec, deadline_vec, volume_vec, dist_mat)
    print(f'Time taken for bundling 1 and 2 and 3: {time.time() - start_time} seconds')

    all_bundles = []
    set_bundles = []
    bike_bundles1 = []
    car_bundles1 = []
    bike_bundles2 = []
    car_bundles2 = []
    bike_bundles3 = []
    bike_bundles4 = []
    car_bundles3 = []
    car_bundles4 = []
    walk_bundles1 = []
    walk_bundles2 = []
    walk_bundles3 = []
    walk_bundles4 = []
    index_mappings = {'walk1': {}, 'walk2': {}, 'bike1': {}, 'car1': {}, 'bike2': {}, 'car2': {}, 'bike3': {},
                      'car3': {}, 'walk3': {}, 'bike4': {}, 'car4': {}, 'bike5': {}, 'car5': {}}

    set_bundles.extend(best_sequences[0]['WALK'])
    index_mappings['walk1'] = {i: bundle for i, bundle in enumerate(best_sequences[0]['WALK'])}
    set_bundles.extend(best_sequences[0]['BIKE'])
    index_mappings['bike1'] = {i: bundle for i, bundle in enumerate(best_sequences[0]['BIKE'])}
    set_bundles.extend(best_sequences[0]['CAR'])
    index_mappings['car1'] = {i: bundle for i, bundle in enumerate(best_sequences[0]['CAR'])}
    set_bundles.extend(best_sequences[1]['WALK'])
    index_mappings['walk2'] = {i: bundle for i, bundle in enumerate(best_sequences[1]['WALK'])}
    set_bundles.extend(best_sequences[1]['BIKE'])
    index_mappings['bike2'] = {i: bundle for i, bundle in enumerate(best_sequences[1]['BIKE'])}
    set_bundles.extend(best_sequences[1]['CAR'])
    index_mappings['car2'] = {i: bundle for i, bundle in enumerate(best_sequences[1]['CAR'])}
    set_bundles.extend(best_sequences[2]['WALK'])
    index_mappings['walk3'] = {i: bundle for i, bundle in enumerate(best_sequences[2]['WALK'])}
    set_bundles.extend(best_sequences[2]['BIKE'])
    index_mappings['bike3'] = {i: bundle for i, bundle in enumerate(best_sequences[2]['BIKE'])}
    set_bundles.extend(best_sequences[2]['CAR'])
    index_mappings['car3'] = {i: bundle for i, bundle in enumerate(best_sequences[2]['CAR'])}

    best_obj = sum((bundle.cost for bundle in all_bundles)) / K
    print(f'Initial Best obj = {best_obj}')

    def are_triplets_feasible(i,j,k,l, bike_feasible_triplets):
        return (frozenset([i, j, l]) in bike_feasible_triplets and
                frozenset([i, k, l]) in bike_feasible_triplets and
                frozenset([j, k, l]) in bike_feasible_triplets)

    def are_triplets_feasible2(i,j,k,l,m, bike_feasible_triplets):
        return (frozenset([i, j, m]) in bike_feasible_triplets and
                frozenset([i, k, m]) in bike_feasible_triplets and
                frozenset([i, l, m]) in bike_feasible_triplets and
                frozenset([j, k, m]) in bike_feasible_triplets and
                frozenset([j, l, m]) in bike_feasible_triplets and
                frozenset([k, l, m]) in bike_feasible_triplets)


    flag = True
    while time.time() - start_time < timelimit and flag:

        walk_counter4 = 0
        walk_feasible_triplets = feasible_triplets_by_rider['WALK']
        for bundle3 in index_mappings['walk3'].values():
            for bundle1 in index_mappings['walk1'].values():
                sorted_seq = sorted(bundle3.shop_seq)
                if bundle1.total_volume + bundle3.total_volume <= walk_rider.capa and bundle1.shop_seq[0] > sorted_seq[2]:
                    if are_triplets_feasible(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0], walk_feasible_triplets):
                        merged_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle3)
                        if merged_bundle is not None:
                            set_bundles.append(merged_bundle)
                            index_mappings['walk4'][(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0])]  = merged_bundle
                        else:
                            walk_counter4 += 1
                            print("Number of times no merged bundle found: ", walk_counter4)

        bike_count4 = 0
        non_feasible_quad = {"BIKE4":{}, "CAR4":{}, "WALK4":{}}
        bike_feasible_triplets = feasible_triplets_by_rider['BIKE']
        for bundle3 in index_mappings['bike3'].values():
            if time.time() - start_time >= timelimit - 14:
                flag = False
                break
            for bundle1 in index_mappings['bike1'].values():
                sorted_seq = sorted(bundle3.shop_seq)
                if bundle1.total_volume + bundle3.total_volume<=bike_rider.capa and bundle1.shop_seq[0]>sorted_seq[2]:
                    if are_triplets_feasible(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0], bike_feasible_triplets):
                        merged_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle3)
                        if merged_bundle is not None:
                            set_bundles.append(merged_bundle)
                            index_mappings['bike4'][(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0])]  = merged_bundle
                            bike_bundles4.append(merged_bundle)
                        else:
                            bike_count4 += 1
                            non_feasible_quad["BIKE4"][(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0])] = (bundle1, bundle3)
                            print("Number of times no merged bundle found: ", bike_count4)

        """
        bike_count5 = 0
        bike_bundles5 = []
        for bundle4 in index_mappings['bike4'].values():
            for bundle1 in index_mappings['bike1'].values():
                sorted_seq = sorted(bundle4.shop_seq)
                if bundle1.total_volume + bundle4.total_volume <= bike_rider.capa and bundle1.shop_seq[0] > sorted_seq[3]:
                    if are_triplets_feasible2(sorted_seq[0], sorted_seq[1], sorted_seq[2], sorted_seq[3], bundle1.shop_seq[0], bike_feasible_triplets):
                        merged_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle4)
                        if merged_bundle is not None:
                            set_bundles.append(merged_bundle)
                            index_mappings['bike5'][(sorted_seq[0], sorted_seq[1], sorted_seq[2], sorted_seq[3], bundle1.shop_seq[0])]  = merged_bundle
                            bike_bundles5.append(merged_bundle)
                        else:
                            bike_count5 += 1
                            print("Number of times no bike merged bundle 5 found: ", bike_count5)
        """

        car_count4 = 0
        car_feasible_triplets = feasible_triplets_by_rider['CAR']
        for bundle3 in index_mappings['car3'].values():
            if time.time() - start_time >= timelimit - 10:
                flag = False
                break
            for bundle1 in index_mappings['car1'].values():
                sorted_seq = sorted(bundle3.shop_seq)
                if bundle1.total_volume+ bundle3.total_volume <= car_rider.capa and bundle1.shop_seq[0]>sorted_seq[2]:
                    if are_triplets_feasible(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0], car_feasible_triplets):
                        merged_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle3)
                        if merged_bundle is not None:
                            set_bundles.append(merged_bundle)
                            index_mappings['car4'][(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0])]  = merged_bundle
                            car_bundles4.append(merged_bundle)
                        else:
                            car_count4 += 1
                            print("Number of times no merged bundle found: ", car_count4)
                            non_feasible_quad["CAR4"][(sorted_seq[0], sorted_seq[1], sorted_seq[2], bundle1.shop_seq[0])] = (bundle1, bundle3)

        """
        car_count5 = 0
        car_bundles5 = []
        for bundle4 in index_mappings['car4'].values():
            for bundle1 in index_mappings['car1'].values():
                sorted_seq = sorted(bundle4.shop_seq)
                if bundle1.total_volume + bundle4.total_volume <= car_rider.capa and bundle1.shop_seq[0] > sorted_seq[3]:
                    if are_triplets_feasible2(sorted_seq[0], sorted_seq[1], sorted_seq[2], sorted_seq[3], bundle1.shop_seq[0], car_feasible_triplets):
                        merged_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle4)
                        if merged_bundle is not None:
                            set_bundles.append(merged_bundle)
                            index_mappings['car5'][(sorted_seq[0], sorted_seq[1], sorted_seq[2], sorted_seq[3], bundle1.shop_seq[0])]  = merged_bundle
                            car_bundles5.append(merged_bundle)
                        else:
                            car_count5 += 1
                            print("Number of times no merged car bundle 5 found: ", car_count5)
        """

        def optimize_bundles(start_time, timelimit, set_bundles, K, gurobi_riders):
            model = gp.Model('Set Covering')

            elements = set(range(0, K))
            # Create variables
            x = model.addVars(len(set_bundles), vtype=GRB.BINARY, name="x")

            model.setObjective(gp.quicksum(x[i] * set_bundles[i].cost for i in range(len(set_bundles))), GRB.MINIMIZE)

            # Add constraints: Each element must be covered exactly once
            element_to_bundle = {element: [] for element in elements}
            for i, bundle in enumerate(set_bundles):
                for element in bundle.shop_seq:
                    element_to_bundle[element].append(i)

            for element, bundles in element_to_bundle.items():
                if len(bundles) == 0:
                    print(f"Warning: Element {element} is not covered by any bundle.")
                else:
                    model.addConstr(gp.quicksum(x[i] for i in bundles) == 1, name=f"cover_{element}")

            # Add constraints: Limited number of each rider type
            rider_to_bundle = {}
            for i, bundle in enumerate(set_bundles):
                rider_type = bundle.rider.type
                if rider_type not in rider_to_bundle:
                    rider_to_bundle[rider_type] = []
                rider_to_bundle[rider_type].append(i)

            for rider_type, bundles in rider_to_bundle.items():
                max_riders = next((rider.available_number for rider in gurobi_riders if rider.type == rider_type), None)
                if max_riders is None:
                    print(f"Warning: No available riders of type {rider_type}. This will cause infeasibility.")
                    max_riders = 0  # Ensure there are no bundles for unavailable riders
                model.addConstr(gp.quicksum(x[i] for i in bundles) <= max_riders, name=f"rider_limit_{rider_type}")

            left_time = max(timelimit - (time.time() - start_time) + 0.6, 0.2)
            model.setParam(GRB.Param.TimeLimit, left_time)
            model.optimize()

            if model.status == GRB.INFEASIBLE:
                print("Model is infeasible. Performing infeasibility analysis.")
                model.computeIIS()
                model.write("model.ilp")
                for constr in model.getConstrs():
                    if constr.IISConstr:
                        print(f"Infeasible constraint: {constr.constrName}")

            # Collect the selected bundles into bundle_set
            all_bundles = [set_bundles[i] for i in range(len(set_bundles)) if x[i].X > 0.5]

            # Display the results
            if model.status == GRB.OPTIMAL:
                print("Optimal solution found:")
                for bundle in all_bundles:
                    print(
                        f"Bundle selected with cost {bundle.cost} and sequence {bundle.shop_seq} using rider {bundle.rider.type}")
            else:
                print("No optimal solution found. Status:", model.status)

            cur_obj = sum(bundle.cost for bundle in all_bundles) / K

            return all_bundles, cur_obj

        all_bundles, cur_obj = optimize_bundles(start_time, timelimit, set_bundles, K, all_riders)

        # Check if the current objective is better than the best one found so far
        if cur_obj < best_obj:
            best_obj = cur_obj
            print(f'num of bundles = {len(all_bundles)}')
            print(f'Best obj = {best_obj}')
            print(f'Computation time = {time.time() - start_time}')
        break

    solution = [
        [bundle.rider.type, bundle.shop_seq, bundle.dlv_seq]
        for bundle in all_bundles
    ]
    cur_obj = (sum(bundle.cost for bundle in all_bundles)) / K
    print(f'Final obj = {cur_obj}')
    print(f'Computation time = {time.time() - start_time}')

    return solution
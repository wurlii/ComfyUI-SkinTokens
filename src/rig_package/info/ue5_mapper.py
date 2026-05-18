import numpy as np
import argparse
import os
import sys
from pathlib import Path
from typing import List

# Add project root to sys.path to allow imports when run as standalone
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.rig_package.parser.bpy import BpyParser

UE5_NAMES = {
    "Pelvis": "pelvis",
    "L_Hip": "thigh_l",
    "L_Knee": "calf_l",
    "L_Ankle": "foot_l",
    "L_Foot": "ball_l",
    "L_Toe": "ball_l",
    "R_Hip": "thigh_r",
    "R_Knee": "calf_r",
    "R_Ankle": "foot_r",
    "R_Foot": "ball_r",
    "R_Toe": "ball_r",
    "Spine1": "spine_01",
    "Spine2": "spine_02",
    "Spine3": "spine_03",
    "Spine4": "spine_04",
    "Spine5": "spine_05",
    "Neck": "neck_01",
    "Head": "neck_02",
    "HeadTop": "head",
    "L_Collar": "clavicle_l",
    "L_Shoulder": "upperarm_l",
    "L_Elbow": "lowerarm_l",
    "L_Wrist": "hand_l",
    "R_Collar": "clavicle_r",
    "R_Shoulder": "upperarm_r",
    "R_Elbow": "lowerarm_r",
    "R_Wrist": "hand_r",
}

for prefix, u_suffix in [("L", "l"), ("R", "r")]:
    for f in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
        for i in [1, 2, 3]:
            UE5_NAMES[f"{prefix}_{f}{i}"] = f"{f.lower()}_0{i}_{u_suffix}"

def map_asset_to_ue5(joints: np.ndarray, parents: np.ndarray) -> List[str]:
    """
    Takes a generated skeleton's joints and parents and returns a list
    of UE5 bone names corresponding to each index.
    Unmatched bones will keep a bone_X format.
    """
    J = len(joints)
    labels = [f"bone_{i}" for i in range(J)]
    
    children = {i: [] for i in range(J)}
    for i in range(J):
        if parents[i] != -1:
            children[parents[i]].append(i)
            
    root_idx = -1
    for i in range(J):
        if parents[i] == -1:
            root_idx = i
            break
            
    if root_idx == -1:
        return labels
        
    labels[root_idx] = "Pelvis"
    
    rc = children[root_idx]
    if not rc: return labels
    
    # Spine is the child pointing highest (max Z)
    spine_idx = max(rc, key=lambda c: joints[c][2])
    hips = [c for c in rc if c != spine_idx]
    
    l_hip_idx, r_hip_idx = -1, -1
    if len(hips) >= 2:
        # Sort by X. Assuming +X is Left (Standard T-Pose)
        hips.sort(key=lambda c: joints[c][0])
        r_hip_idx = hips[0]
        l_hip_idx = hips[-1]
    elif len(hips) == 1:
        if joints[hips[0]][0] > 0:
            l_hip_idx = hips[0]
        else:
            r_hip_idx = hips[0]
            
    def label_chain(start, child_map, names):
        curr = start
        for name in names:
            if curr == -1: break
            labels[curr] = name
            if not child_map[curr]: break
            curr = child_map[curr][0]
            
    if l_hip_idx != -1:
        label_chain(l_hip_idx, children, ["L_Hip", "L_Knee", "L_Ankle", "L_Foot", "L_Toe"])
    if r_hip_idx != -1:
        label_chain(r_hip_idx, children, ["R_Hip", "R_Knee", "R_Ankle", "R_Foot", "R_Toe"])
        
    curr = spine_idx
    spine_count = 1
    while curr != -1:
        c = children[curr]
        if len(c) == 1:
            labels[curr] = f"Spine{spine_count}"
            spine_count += 1
            curr = c[0]
        elif len(c) >= 3:
            labels[curr] = f"Spine{spine_count}"
            
            # Neck is highest Z
            neck_idx = max(c, key=lambda x: joints[x][2])
            collars = [x for x in c if x != neck_idx]
            collars.sort(key=lambda x: joints[x][0])
            r_collar_idx = collars[0] if len(collars) > 0 else -1
            l_collar_idx = collars[-1] if len(collars) > 1 else -1
            
            label_chain(neck_idx, children, ["Neck", "Head", "HeadTop"])
            
            def label_fingers(wrist_idx, prefix):
                fingers = children[wrist_idx]
                if not fingers: return
                # Thumb is the shortest vector from wrist
                thumb_idx = min(fingers, key=lambda f: np.linalg.norm(joints[f] - joints[wrist_idx]))
                other_fingers = [f for f in fingers if f != thumb_idx]
                # Sort other 4 fingers by Y (forward to back, ascending)
                # Lowest Y is front (Index), Highest Y is back (Pinky)
                other_fingers.sort(key=lambda f: joints[f][1], reverse=False)
                
                label_chain(thumb_idx, children, [f"{prefix}_Thumb1", f"{prefix}_Thumb2", f"{prefix}_Thumb3"])
                finger_names = ["Index", "Middle", "Ring", "Pinky"]
                for i, f_idx in enumerate(other_fingers):
                    if i >= 4: break
                    name = finger_names[i]
                    label_chain(f_idx, children, [f"{prefix}_{name}1", f"{prefix}_{name}2", f"{prefix}_{name}3"])
            
            if l_collar_idx != -1:
                label_chain(l_collar_idx, children, ["L_Collar", "L_Shoulder", "L_Elbow", "L_Wrist"])
                l_wrist = -1
                for w in range(J):
                    if labels[w] == "L_Wrist": l_wrist = w; break
                if l_wrist != -1:
                    label_fingers(l_wrist, "L")
                    
            if r_collar_idx != -1:
                label_chain(r_collar_idx, children, ["R_Collar", "R_Shoulder", "R_Elbow", "R_Wrist"])
                r_wrist = -1
                for w in range(J):
                    if labels[w] == "R_Wrist": r_wrist = w; break
                if r_wrist != -1:
                    label_fingers(r_wrist, "R")
            
            break
        else:
            labels[curr] = f"Spine{spine_count}"
            break

    # Convert semantic labels to UE5
    final_names = []
    for label in labels:
        if label in UE5_NAMES:
            final_names.append(UE5_NAMES[label])
        else:
            final_names.append(label)
            
    return final_names

def main():
    parser = argparse.ArgumentParser(description="Standalone UE5 Bone Mapper")
    parser.add_argument("--input", required=True, help="Path to input 3D file (fbx, glb, obj)")
    parser.add_argument("--output", help="Path to output file (default: input_ue5.ext)")
    parser.add_argument("--format", choices=["glb", "fbx", "obj"], help="Force output format")
    
    args = parser.parse_args()
    
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Error: File {in_path} does not exist.")
        return

    # Determine output path
    if args.output:
        out_path = Path(args.output).resolve()
    else:
        ext = args.format if args.format else in_path.suffix[1:]
        out_path = in_path.with_name(f"{in_path.stem}_ue5.{ext}")

    print(f"Loading {in_path}...")
    asset = BpyParser.load(str(in_path))
    
    print("Mapping bones to UE5...")
    original_names = asset.joint_names.copy() if asset.joint_names is not None else [f"bone_{i}" for i in range(len(asset.joints))]
    new_names = map_asset_to_ue5(asset.joints, asset.parents)
    asset.joint_names = new_names
    
    print("\nBone Mapping Log:")
    print("-" * 40)
    for old, new in zip(original_names, new_names):
        if old != new:
            print(f"  {old} -> {new}")
    print("-" * 40 + "\n")
    
    print(f"Exporting to {out_path}...")
    BpyParser.export(asset, str(out_path))
    print("Done!")

if __name__ == "__main__":
    main()

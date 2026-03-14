import os
import shutil

merged_folder = "merged_dataset"
os.makedirs(merged_folder, exist_ok=True)

############################################
# COPY HAM10000 (7 classes)
############################################

ham_folder = "HAM10000_images"

for class_name in os.listdir(ham_folder):
    src_class = os.path.join(ham_folder, class_name)

    if os.path.isdir(src_class):
        dst_class = os.path.join(merged_folder, class_name)
        os.makedirs(dst_class, exist_ok=True)

        for img in os.listdir(src_class):
            shutil.copy(
                os.path.join(src_class, img),
                os.path.join(dst_class, img)
            )

print("HAM10000 copied successfully!")

############################################
# COPY SELECTED SD-198 CLASSES
############################################

sd_folder = "SD-198"

selected_classes = [
    "Acne_Vulgaris","Acne_Keloidalis_Nuchae","Steroid_Acne","Pomade_Acne",
    "Pseudofolliculitis_Barbae",
    "Acute_Eczema","Dry_Skin_Eczema","Dyshidrosiform_Eczema",
    "Allergic_Contact_Dermatitis","Seborrheic_Dermatitis",
    "Perioral_Dermatitis","Nummular_Eczema",
    "Tinea_Corporis","Tinea_Cruris","Tinea_Faciale","Tinea_Manus",
    "Tinea_Pedis","Tinea_Versicolor","Onychomycosis",
    "Herpes_Simplex_Virus","Herpes_Zoster","Impetigo",
    "Molluscum_Contagiosum","Varicella","Wound_Infection","Cellulitis",
    "Psoriasis","Scalp_Psoriasis","Pustular_Psoriasis","Guttate_Psoriasis",
    "Melasma","Vitiligo","Solar_Lentigo","Cafe_Au_Lait_Macule",
    "Skin_Tag","Keloid","Lipoma","Scar","Callus"
]

for class_name in selected_classes:
    src_class = os.path.join(sd_folder, class_name)

    if os.path.exists(src_class):
        dst_class = os.path.join(merged_folder, class_name)
        os.makedirs(dst_class, exist_ok=True)

        for img in os.listdir(src_class):
            shutil.copy(
                os.path.join(src_class, img),
                os.path.join(dst_class, img)
            )

print("Selected SD-198 classes copied!")
print("FINAL 40-CLASS DATASET READY!")
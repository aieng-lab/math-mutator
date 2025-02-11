import argparse
import os
import zipfile

import gdown
import gzip
import shutil

this_dir = os.path.dirname(os.path.realpath(__file__))

def download_arqmath(path):
    files = {
        'https://drive.google.com/file/d/1jrDxE_NtIrZXh7o6OuJNQg233YrpQga8/view?usp=drive_link': 'Votes.V1.3.xml',
        'https://drive.google.com/file/d/1bUxHKTu9zDwq1TFPDRU213pDDN40RKX1/view?usp=drive_link': 'Users.V1.3.xml',
        'https://drive.google.com/file/d/1fcLhlJqGaXm3J2_b4yar7mLe8Oau1kbQ/view?usp=drive_link': 'Tags.V1.3.xml',
        'https://drive.google.com/file/d/14SSwTqLZgLVP6iDsAJbmxgb01a8NYyDb/view?usp=drive_link': 'Posts.V1.3.xml',
        'https://drive.google.com/file/d/1AjZ2SDH7XSG5xKwfqpXwwvJkUuQuL0pr/view?usp=drive_link': 'PostLinks.V1.3.xml',
        'https://drive.google.com/file/d/1vDn_8sCHm_6lg4JuJBxlVsUEPU5KL4Mv/view?usp=drive_link': 'Comments.V1.3.xml',
        'https://drive.google.com/file/d/1bFrbVf2WFFAKfTrv3L2DgZWuk6DQ_oL2/view?usp=drive_link': 'Badges.V1.3.xml'
    }

    file_prefix = f'{path}/arqmath/'
    os.makedirs(file_prefix, exist_ok=True)

    for id, name in files.items():
        print(name)
        file_name = file_prefix + name
        if not os.path.isfile(file_name):
            try:
                gdown.download(id, file_name, quiet=False, fuzzy=True)
            except ValueError as e:
                print("Could not download file %s (%s)" % (name, e))



    latex_file = 'https://drive.google.com/file/d/1WNrDGmrrPWb24WUKN2RKyR1lGn4O6wYu/view?usp=drive_link'
    output = f'{path}/raw/latex_representation_v3.zip'
    os.makedirs(f'{path}/raw', exist_ok=True)
    gdown.download(latex_file, output, quiet=False, fuzzy=True)

    # Step 2: Extract the .zip file
    print(f"Extracting files to {file_prefix}...")

    with zipfile.ZipFile(output, 'r') as zip_ref:
        zip_ref.extractall(file_prefix)

    print(f"Extraction completed. Files are in '{file_prefix}'.")

    # Step 3: (Optional) List extracted files
    print("Extracted files:")
    for root, dirs, files in os.walk(file_prefix):
        for file in files:
            print(os.path.join(root, file))


def download_amps(path):
    id = 'https://drive.google.com/file/d/%s/view?usp=drive_link' % id
    file_prefix = f'{path}/raw/amps/'
    file_name = file_prefix + 'amps.tar.gz'
    if not os.path.isfile(file_name):
        os.makedirs(file_prefix, exist_ok=True)
        try:
            gdown.download(id, file_name, quiet=False, fuzzy=True)
        except ValueError as e:
            print("Could not download file %s (%s)" % (file_name, e))
            raise e

        print("Downloaded amps data")
    else:
        print("%s already downloaded" % file_name)

    zip_file = file_prefix + 'amps.tar'
    if not os.path.isfile(zip_file):
        with gzip.open(file_name, 'rb') as f_in:
            with open(zip_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print('Extracted gz')


    zip_file = file_prefix + 'amps.tar'
    import tarfile
    with tarfile.open(zip_file) as tar:
        tar.extractall(path=path)

    print('Extracted zip for AMPS')



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default=f'{this_dir}/data')
    parser.add_argument('--amps', type=bool, default=False)
    parser.add_argument('--arqmath', type=bool, default=True)
    args = parser.parse_args()

    if args.amps:
        download_amps(args.path)

    if args.arqmath:
        download_arqmath(args.path)

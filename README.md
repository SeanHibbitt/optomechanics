# Optomechanics


## SSH git access
Since you'll likely have a SSH key per repo per computer, you'll need to make sure to add the correct SSH config to direct between ssh keys, e.g:

Host OptomechanicsGithub

  Hostname github.com
  
  User git
  
  IdentityFile ~/.ssh/GitHubOptomechanics
  
  IdentitiesOnly yes


Host RoomTempGithub

  Hostname github.com
  
  User git
  
  IdentityFile ~/.ssh/id_ecdsa_RT2024_data
  
  IdentitiesOnly yes
  


CMD: git clone "git@OptomechanicsGithub:SeanHibbitt/Optomechanics.git"


## updating the exp module yml file from your own:

  Before updating, rebuild from the latest yml file! PLEASE!

  Then run the following command to generate, make sure you're in the correct folder:
    conda env export > ExperimentsEnvironment.yml

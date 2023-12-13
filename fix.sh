git filter-branch --commit-filter '

    # check to see if the committer (email is the desired one)
    if [ "$GIT_COMMITTER_EMAIL" != "12870244+lachlanshoesmith@users.noreply.github.com" ];
    then
            # Set the new desired name
            GIT_COMMITTER_NAME="lachlanshoesmith";
            GIT_AUTHOR_NAME="lachlanshoesmith";

            # Set the new desired email
            GIT_COMMITTER_EMAIL="12870244+lachlanshoesmith@users.noreply.github.com";
            GIT_AUTHOR_EMAIL="12870244+lachlanshoesmith@users.noreply.github.com";

            # (re) commit with the updated information
            git commit-tree "$@";
    else
            # No need to update so commit as is
            git commit-tree "$@";
    fi' 
HEAD

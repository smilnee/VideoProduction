# Repository visibility and access

The [smilnee/VideoProduction template](https://github.com/smilnee/VideoProduction)
is public at the owner's explicit request on 2026-11-02, superseding its initial
private publication and earlier Bentley-only sharing request. Anyone can read,
clone or download the repository and its published history without a GitHub
login. It is not restricted to Bentley or any email domain.

Public read access does not grant write or administrator access. GitHub Copilot
still requires its own sign-in/entitlement, and application licences, model
availability and organization policies still apply. The public template contains
reusable workflow/integration sources, not project models, footage, credentials
or machine-specific MCP settings. Do not publish those when using it.

Making a repository private later cannot recall copies already downloaded.
The guidance below applies if restricted sharing is requested again; it is not
a description of the current public repository.

## A personal repository is not an email-domain gate

GitHub personal repositories authorize the owner and invited collaborators.
There is no repository setting that admits only logins ending `@bentley.com`.
A profile email, an invitation email or domain verification alone is not that
authentication control. Private visibility prevents public access but does not
enforce Bentley corporate identity.

The `smilnee/VideoProduction` destination is under a personal GitHub account.
Do not describe it as Bentley-SSO-enforced. For future restricted sharing,
either agree a manually approved private collaborator policy or move to the
managed-organization route; manual invitations are not domain enforcement.

## For future organization-only sharing

A Bentley GitHub/identity administrator must confirm:

1. The authorized Bentley-managed organization and destination repository.
2. Enforced corporate SSO or the enterprise's equivalent managed-identity
   controls. For SAML SSO, GitHub requires Enterprise Cloud. Merely enabling
   optional SSO does not enforce it.
3. Identity-provider assignment and group membership restricted to approved
   Bentley corporate identities. An email suffix alone does not establish
   employment or prevent guest access.
4. A private repository and the intended team/permission. Verify inherited
   organization base access and administrator access as well as team grants.
5. No unintended direct grants, outside collaborators, pending invitations,
   deploy keys or app/integration access. Standard organization SAML does not
   require outside collaborators to authenticate with SSO; that exception must
   not become a way around the intended restriction.
6. The credential used to publish is authorized for the organization. Do not
   collect passwords/tokens in chat or broaden identity policies automatically.

Organization-wide SSO enforcement can remove members who have not authenticated.
It is a separate administrator change, not a safe side effect of publishing this
template. Do not enable it across an existing organization without explicit,
properly scoped approval.

## Verify publication

- Inspect the existing destination before creating or modifying a repository.
  Do not overwrite another project's history or make an unrelated repository
  private. Ask if the owner or intended access model is ambiguous.
- Use the owner's explicitly approved visibility. Default new destinations to
  private unless public release is authorized. Before making a repository
  public, review all reachable published history as well as current files for
  secrets, personal paths, proprietary project data and unapproved source.
  Upload only reviewed template documentation/customizations, validation code
  and approved integration sources, not model files, footage,
  editor projects, local evidence, tokens or machine-specific settings.
- If GitHub's template setting is wanted, enable and verify `is_template`
  separately from visibility. Do not assume a copied repository inherits
  private visibility, SSO or team access.
- Read back `private`/visibility, owner, default branch, template status, latest
  commit and effective access grants. For public access, also verify anonymous
  retrieval without an Authorization header. Verify any claimed SSO/identity
  restrictions through authorized administrator evidence, not visibility alone.
- Report publication and identity enforcement as separate PASS/unresolved
  results. If authentication or the organization is missing, retain the local
  deliverable and state the blocker; do not claim a repository URL is live.

## GitHub references

- [Personal repository permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository)
- [Authentication with SSO, including the outside-collaborator exception](https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-single-sign-on/about-authentication-with-single-sign-on)
- [Enforcing organization SAML SSO](https://docs.github.com/en/enterprise-cloud@latest/organizations/managing-saml-single-sign-on-for-your-organization/enforcing-saml-single-sign-on-for-your-organization)

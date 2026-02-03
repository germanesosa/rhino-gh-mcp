using System;
using System.Drawing;
using Grasshopper;
using Grasshopper.Kernel;

namespace rhino_gh_mcp
{
    public class rhino_gh_mcpInfo : GH_AssemblyInfo
    {
        public override string Name => "rhino_gh_mcp Info";

        //Return a 24x24 pixel bitmap to represent this GHA library.
        public override Bitmap Icon => null;

        //Return a short string describing the purpose of this GHA library.
        public override string Description => "";

        public override Guid Id => new Guid("0da4125f-25e9-4e6d-87bf-efeaff5ac551");

        //Return a string identifying you or your company.
        public override string AuthorName => "";

        //Return a string representing your preferred contact details.
        public override string AuthorContact => "";

        //Return a string representing the version.  This returns the same version as the assembly.
        public override string AssemblyVersion => GetType().Assembly.GetName().Version.ToString();
    }
}
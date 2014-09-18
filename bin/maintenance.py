'''
Perform maintenance operations on source code.
'''
from ben10.filesystem import CreateFile, FindFiles, GetFileLines
from clikit.app import App



app = App('maintenance')

@app
def license_headers(console_, directory, header='HEADER.txt'):
    '''
    Check and fix license headers in all source files.

    :param directory: The base directory perform the operation.
    :param header: Filename containing the header information.
    '''

    def MatchHeader(lines, header_lines):
        '''
        Returns whether the given filename lines (lines) match the header lines (header_lines).
        '''
        if len(lines) < len(header_lines):
            return False
        lines = lines[:len(header_lines)]
        for i, j in zip(lines, header_lines):
            if i != j.strip():
                return False
        return True

    header_lines = GetFileLines(header)
    filenames = FindFiles(directory, in_filters=['*.py'])
    for i_filename in filenames:
        console_.Progress(i_filename + '... ')

        # Get filename lines.
        lines = GetFileLines(i_filename)

        # Check if we already have the proper header.
        if MatchHeader(lines, header_lines):
            console_.ProgressWarning('skip')
            continue

        # Add/replace header with our header.
        content = []
        for i_line in lines:
            if not content and i_line.startswith('#'):
                continue
            content.append(i_line)
        content = header_lines + content

        # Rewrite the file.
        CreateFile(i_filename, '\n'.join(content))
        console_.ProgressOk('done')



if __name__ == '__main__':
    app.Main()
